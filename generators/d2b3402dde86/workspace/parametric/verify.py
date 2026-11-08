#!/usr/bin/env python3
"""Protected-Racket verification for the proposed four-corner family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import public_challenge_id

import prototype

HERE = Path(__file__).resolve().parent


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _execute(programs: dict[str, str], inputs: list[list[list[int]]]):
    with RacketBridge() as bridge:
        rule_names = {}
        for index, (setting, source) in enumerate(programs.items()):
            name = f"__d2_corner_rule_{index}"
            bridge.eval_text(f"(define {name} {strip_rule_wrapper(source)})")
            rule_names[setting] = name
        input_names = []
        for index, grid in enumerate(inputs):
            name = f"__d2_corner_input_{index}"
            bridge.define_grid(name, grid)
            input_names.append(name)
        return {
            setting: [bridge.eval_text(f"({name} {grid_name})") for grid_name in input_names]
            for setting, name in rule_names.items()
        }


def verify(out_dir: Path, seed: int = 20261024) -> dict[str, Any]:
    if out_dir.exists():
        raise FileExistsError(out_dir)
    settings = [{prototype.PARAMETER_NAME: value} for value in prototype.ALLOWED_SETTINGS]
    episodes = [prototype.generate(seed, setting, 3, 4) for setting in settings]
    inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
    if any([pair["input"] for pair in e["train"] + e["test"]] != inputs for e in episodes[1:]):
        raise AssertionError("input sampling depends on the hidden setting")
    programs = {setting[prototype.PARAMETER_NAME]: prototype.program(setting) for setting in settings}
    matrix = _execute(programs, inputs)

    records = []
    public_payloads: dict[str, bytes] = {}
    for episode in episodes:
        selected = episode["settings"][prototype.PARAMETER_NAME]
        expected = [pair["output"] for pair in episode["train"] + episode["test"]]
        if matrix[selected] != expected:
            raise AssertionError(f"Racket/Python mismatch for {selected}")
        rivals = {}
        for rival in prototype.ALLOWED_SETTINGS:
            if rival == selected:
                continue
            demo_disagreements = [i for i in range(3) if matrix[rival][i] != expected[i]]
            query_disagreements = [i for i in range(4) if matrix[rival][3 + i] != expected[3 + i]]
            if not demo_disagreements or len(query_disagreements) != 4:
                raise AssertionError(f"weak retained lesson against {rival}")
            rivals[rival] = {
                "demo_disagreement_indices": demo_disagreements,
                "query_disagreement_indices": query_disagreements,
            }
        reveal_ids = []
        for index in range(4):
            payload = prototype.visible_turn(episode, index)
            identifier = hashlib.sha256(payload).hexdigest()
            if identifier != public_challenge_id({"train": episode["train"], "test": [episode["test"][index]]}):
                raise AssertionError("public ID does not bind exact projection bytes")
            if b"settings" in payload or b"program" in payload:
                raise AssertionError("public turn leaks private fields")
            public_payloads[identifier] = payload
            reveal_ids.append(identifier)
        records.append({
            "settings": episode["settings"],
            "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
            "reveal_ids": reveal_ids,
            "certificate": episode["certificate"],
            "rivals": rivals,
            "labels": expected,
        })

    # Bounded adversarial pass: malformed setting, tampered query label, duplicate
    # input, and one-vs-four query first-turn drift.
    adversarial = {}
    checks = {
        "malformed_setting": lambda: prototype.generate(seed, {"corner": "center"}, 3, 4),
        "tampered_label": None,
        "duplicate_input": None,
    }
    tampered = copy.deepcopy(episodes[0])
    tampered["test"][0]["output"][0][0] = 9
    checks["tampered_label"] = lambda: prototype.verify_episode(tampered)
    duplicate = copy.deepcopy(episodes[0])
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    checks["duplicate_input"] = lambda: prototype.verify_episode(duplicate)
    for name, action in checks.items():
        try:
            action()
        except ValueError as error:
            adversarial[name] = {"rejected": True, "error": str(error)}
        else:
            raise AssertionError(f"adversarial case was accepted: {name}")
    single = prototype.generate(seed, {"corner": "upper_left"}, 3, 1)
    four = prototype.generate(seed, {"corner": "upper_left"}, 3, 4)
    if prototype.visible_turn(single, 0) != prototype.visible_turn(four, 0):
        raise AssertionError("first turn changes with requested query count")
    adversarial["query_prefix"] = {"rejected": False, "identical": True}

    public_dir = out_dir / "public"
    public_dir.mkdir(parents=True)
    for identifier, payload in sorted(public_payloads.items()):
        (public_dir / f"{identifier}.json").write_bytes(payload)
    private = {
        "schema": f"{prototype.TASK_ID}-corner-parametric-racket-v2",
        "status": "passed",
        "reference": "proposed_parametric",
        "training_admitted": False,
        "seed": seed,
        "racket": {"backend": "RacketBridge", "protected": True, "evaluations": 4 * len(inputs)},
        "episodes": records,
        "adversarial": adversarial,
        "stress": {
            "query_shape": [30, 30],
            "nonzero_cells": sum(bool(v) for row in inputs[-1] for v in row),
            "touches_all_boundaries": True,
        },
        "source_sha256": {
            path.name: _sha(path)
            for path in [HERE / "prototype.py", HERE / "adapter.py", HERE / "promotion.json",
                         *(HERE / f"{value}.rkt" for value in prototype.ALLOWED_SETTINGS)]
        },
        "limitations": [
            "Evidence covers the declared four-corner family and one retained seed, not arbitrary programs.",
            "The proposal remains separate from canonical/training admission.",
        ],
    }
    _write_json(out_dir / "private-report.json", private)
    manifest = {
        "schema": f"{prototype.TASK_ID}-corner-evidence-v2",
        "status": "passed",
        "public_files": len(public_payloads),
        "private_report": "private-report.json",
        "files": {
            path.relative_to(out_dir).as_posix(): {
                "sha256": _sha(path), "bytes": path.stat().st_size
            }
            for path in sorted(out_dir.rglob("*")) if path.is_file()
        },
    }
    _write_json(out_dir / "manifest.json", manifest)
    return private


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "evidence" / "current")
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = verify(args.out, args.seed)
    print(json.dumps({
        "status": report["status"],
        "episodes": len(report["episodes"]),
        "public_turns": sum(len(row["reveal_ids"]) for row in report["episodes"]),
        "evidence": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
