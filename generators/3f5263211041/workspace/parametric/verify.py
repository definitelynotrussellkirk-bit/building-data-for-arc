#!/usr/bin/env python3
"""Build bounded protected-Racket, teaching, export, and causal evidence."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "3f5263211041"
HERE = Path(__file__).resolve().parent
MODES = ("direct", "width_relay")


def _load(filename: str):
    path = (HERE / filename).resolve()
    if path.parent != HERE or not path.is_file():
        raise FileNotFoundError(path)
    name = "_arc_verify_3f5263211041_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P = _load("prototype.py")
A = _load("adapter.py")


def _raw(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_raw(value))


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _digest(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def build(output: Path) -> dict[str, Any]:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"evidence destination is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    programs = {mode: A.program({"gallery_mode": mode}) for mode in MODES}
    wrapped = {mode: wrap_rule(source) for mode, source in programs.items()}
    failures: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    examples: dict[str, Any] = {}
    public_payloads: dict[str, bytes] = {}
    causal_case: dict[str, Any] | None = None
    cache: dict[tuple[str, str], list[list[int]]] = {}

    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket backend required")

        def apply(mode: str, grid: list[list[int]]) -> list[list[int]]:
            key = mode, _digest(grid)
            if key not in cache:
                cache[key] = bridge.eval_text(f"({wrapped[mode]} {_literal(grid)})")
            return deepcopy(cache[key])

        for seed in (0, 17):
            matched: list[str] | None = None
            for mode in MODES:
                settings = {"gallery_mode": mode}
                episode = A.generate(seed, settings, 3, 4)
                inputs = [_digest(pair["input"]) for pair in episode["train"] + episode["test"]]
                if matched is None:
                    matched = inputs
                elif inputs != matched:
                    failures.append({"kind": "settings_inputs_not_matched", "seed": seed, "mode": mode})
                mismatches = [
                    index
                    for index, pair in enumerate(episode["train"] + episode["test"])
                    if apply(mode, pair["input"]) != pair["output"]
                ]
                if mismatches:
                    failures.append({"kind": "racket_label_mismatch", "seed": seed, "mode": mode, "indexes": mismatches})
                survivors = [
                    candidate
                    for candidate in MODES
                    if all(apply(candidate, pair["input"]) == pair["output"] for pair in episode["train"])
                ]
                if survivors != [mode]:
                    failures.append({"kind": "finite_setting_survivors", "seed": seed, "mode": mode, "survivors": survivors})
                teaching = P.teaching_check(episode, settings)
                if teaching["harmful_survivors"]:
                    failures.append({"kind": "harmful_named_rival", "seed": seed, "mode": mode, "rivals": teaching["harmful_survivors"]})
                jobs.append({
                    "seed": seed,
                    "settings": settings,
                    "demos": 3,
                    "queries": 4,
                    "survivors": survivors,
                    "teaching": teaching,
                    "input_sha256": inputs,
                    "shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["train"] + episode["test"]],
                    "program_sha256": hashlib.sha256(programs[mode].encode()).hexdigest(),
                })
                if seed == 0:
                    examples[mode] = episode
                    for query_index in range(4):
                        visible = P.public_view(episode, query_index)
                        raw = public_challenge_bytes(visible)
                        public_id = public_challenge_id(visible)
                        if public_id != hashlib.sha256(raw).hexdigest():
                            failures.append({"kind": "public_id_mismatch", "mode": mode, "query": query_index})
                        if public_id in public_payloads:
                            failures.append({"kind": "duplicate_public_payload", "public_id": public_id})
                        public_payloads[public_id] = raw
                    if mode == "width_relay" and causal_case is None:
                        for pair in episode["test"]:
                            facts = P.analyze_input(pair["input"])
                            intended = apply("width_relay", pair["input"])
                            wrong = bridge.eval_text(
                                f"({wrap_rule((HERE / 'height_relay_counterfactual.rkt').read_text(encoding='utf-8'))} {_literal(pair['input'])})"
                            )
                            if intended != wrong:
                                causal_case = {
                                    "input": pair["input"],
                                    "settings": settings,
                                    "intermediate_value": facts["relay_width"],
                                    "wrong_intermediate_value": facts["control_height"],
                                    "output": intended,
                                    "counterfactual_output": wrong,
                                    "program": programs["width_relay"],
                                    "counterfactual_program": (HERE / "height_relay_counterfactual.rkt").read_text(encoding="utf-8"),
                                    "ablation": "wrong_intermediate",
                                    "input_analysis": facts,
                                }
                                break

    for mode in MODES:
        settings = {"gallery_mode": mode}
        two_one = A.generate(5, settings, 2, 1)
        two_four = A.generate(5, settings, 2, 4)
        six_four = A.generate(5, settings, 6, 4)
        if two_one["train"] != two_four["train"] or two_one["test"][0] != two_four["test"][0]:
            failures.append({"kind": "query_prefix_instability", "mode": mode})
        if six_four["train"][:2] != two_four["train"] or six_four["test"] != two_four["test"]:
            failures.append({"kind": "demo_prefix_instability", "mode": mode})

    if causal_case is None:
        failures.append({"kind": "missing_causal_counterfactual"})
    for mode, episode in examples.items():
        _write(output / "examples" / f"{mode}-private.json", episode)
    for public_id, raw in sorted(public_payloads.items()):
        path = output / "public" / f"{public_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    if causal_case is not None:
        _write(output / "causal-case.json", causal_case)
    summary = {
        "schema": "arcpuzzles-3f5263211041-width-relay-authoring-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "racket": identity,
        "jobs": jobs,
        "racket_evaluations": len(cache) + (1 if causal_case is not None else 0),
        "public_files": len(public_payloads),
        "programs": {mode: hashlib.sha256(source.encode()).hexdigest() for mode, source in programs.items()},
        "source_generator_sha256": P._BASE_SHA256,
        "causal_case_path": "causal-case.json" if causal_case is not None else None,
        "failures": failures,
        "limits": "Two seeds, three demonstrations, four queries, two settings, and finite named rivals; not universal proof.",
    }
    _write(output / "summary.json", summary)
    if failures:
        raise AssertionError(json.dumps(failures, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    summary = build(Path(args.out))
    print(json.dumps({
        "status": summary["status"],
        "jobs": len(summary["jobs"]),
        "racket_evaluations": summary["racket_evaluations"],
        "public_files": summary["public_files"],
        "causal_case_path": summary["causal_case_path"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
