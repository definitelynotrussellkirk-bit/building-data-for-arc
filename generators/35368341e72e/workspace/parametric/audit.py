#!/usr/bin/env python3
"""Bounded protected-Racket audit and causal-case builder for 35368341e72e."""
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


HERE = Path(__file__).resolve().parent
TASK_ID = "35368341e72e"
ASSEMBLIES = ("query_order", "fewest_cells_first")


def _load(name: str):
    path = HERE / f"{name}.py"
    module_name = f"_audit_{TASK_ID}_{name}_{hashlib.sha256(str(path).encode()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


ADAPTER = _load("adapter")
PROTOTYPE = _load("prototype")


def _raw(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _sha(value: Any) -> str:
    return hashlib.sha256(_raw(value)).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_new(path: Path, value: Any) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(
        (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()
    )
    temporary.replace(path)


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


class Evaluator:
    def __init__(self) -> None:
        self.bridge = RacketBridge()
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            raise ValueError("audit requires a live protected Racket backend")
        self.identity = {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        }
        self.wrapped: dict[str, str] = {}
        self.evaluations = 0

    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        if program not in self.wrapped:
            self.wrapped[program] = wrap_rule(program)
        result = self.bridge.eval_text(f"({self.wrapped[program]} {_literal(grid)})")
        self.evaluations += 1
        if (
            type(result) is not list
            or not result
            or type(result[0]) is not list
            or not result[0]
            or any(
                type(row) is not list
                or len(row) != len(result[0])
                or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                for row in result
            )
        ):
            raise ValueError("Racket program returned a non-grid")
        return result

    def close(self) -> None:
        self.bridge.close()


def _public_projection(episode: dict[str, Any], assembly: str) -> dict[str, Any]:
    visible = PROTOTYPE.public_turn(episode, 0)
    payload = public_challenge_bytes(visible)
    parsed = json.loads(payload)
    changed = deepcopy(episode)
    changed["settings"] = {"assembly": "query_order"}
    changed["seed"] = -1
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[0]]
    changed["test"][1]["input"] = [[9]]
    changed_payload = public_challenge_bytes(PROTOTYPE.public_turn(changed, 0))
    direct = public_challenge_bytes(
        {"train": episode["train"], "test": [episode["test"][0]]}
    )
    return {
        "public_id": public_challenge_id(visible),
        "public_sha256": hashlib.sha256(payload).hexdigest(),
        "query_answers_hidden": all(set(pair) == {"input"} for pair in parsed["test"]),
        "future_queries_hidden": len(parsed["test"]) == 1,
        "private_mutation_stable": changed_payload == payload,
        "settings_hidden": assembly.encode() not in payload and b"assembly" not in payload,
        "program_hidden": b"rule!" not in payload and b"program_solution" not in payload,
        "first_turn_matches_direct_projection": payload == direct,
    }


def _job(evaluator: Evaluator, seed: int, demos: int, assembly: str) -> tuple[dict[str, Any], dict[str, Any]]:
    settings = {"assembly": assembly}
    episode = ADAPTER.generate(seed, settings, demos, 4)
    programs = {name: ADAPTER.program({"assembly": name}) for name in ASSEMBLIES}
    declared_survivors = []
    for name, program in programs.items():
        outputs = [evaluator.apply(program, pair["input"]) for pair in episode["train"]]
        if all(output == pair["output"] for output, pair in zip(outputs, episode["train"], strict=True)):
            declared_survivors.append(name)
    if declared_survivors != [assembly]:
        raise ValueError(
            f"demonstrations do not identify {assembly}: survivors={declared_survivors}, seed={seed}, demos={demos}"
        )
    selected_program = programs[assembly]
    actual = [
        evaluator.apply(selected_program, pair["input"])
        for pair in episode["train"] + episode["test"]
    ]
    claimed = [pair["output"] for pair in episode["train"] + episode["test"]]
    matches = [left == right for left, right in zip(actual, claimed, strict=True)]
    if not all(matches):
        raise ValueError("Python label differs from protected Racket")
    teaching = PROTOTYPE.teaching_check(episode, settings)
    if teaching["survivors"] != [assembly] or teaching["harmful_survivors"]:
        raise ValueError(f"finite teaching audit failed: {teaching}")
    metrics = [PROTOTYPE.input_metrics(pair["input"]) for pair in episode["train"] + episode["test"]]
    public = _public_projection(episode, assembly)
    if not all(
        public[key]
        for key in (
            "query_answers_hidden",
            "future_queries_hidden",
            "private_mutation_stable",
            "settings_hidden",
            "program_hidden",
            "first_turn_matches_direct_projection",
        )
    ):
        raise ValueError(f"public projection failed: {public}")
    row = {
        "seed": seed,
        "demos": demos,
        "queries": 4,
        "assembly": assembly,
        "program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
        "declared_survivors": declared_survivors,
        "tested_survivors": teaching["survivors"],
        "tested_harmful_survivors": teaching["harmful_survivors"],
        "tested_rivals": sorted(PROTOTYPE.CANDIDATES),
        "all_python_labels_match_racket": all(matches),
        "per_query_racket_match": matches[demos:],
        "input_sha256": [_sha(pair["input"]) for pair in episode["train"] + episode["test"]],
        "demo_shapes": [metric["input_shape"] for metric in metrics[:demos]],
        "query_shapes": [metric["input_shape"] for metric in metrics[demos:]],
        "largest_query_metrics": metrics[-1],
        "public_projection": public,
    }
    private = {"settings": settings, "episode": episode}
    return row, private


def run(seeds: list[int], demo_counts: list[int]) -> tuple[dict[str, Any], dict[str, Any]]:
    evaluator = Evaluator()
    try:
        rows: list[dict[str, Any]] = []
        private: list[dict[str, Any]] = []
        for seed in seeds:
            for demos in demo_counts:
                paired = []
                for assembly in ASSEMBLIES:
                    row, hidden = _job(evaluator, seed, demos, assembly)
                    rows.append(row)
                    private.append(hidden)
                    paired.append(hidden["episode"])
                left_inputs = [p["input"] for p in paired[0]["train"] + paired[0]["test"]]
                right_inputs = [p["input"] for p in paired[1]["train"] + paired[1]["test"]]
                if left_inputs != right_inputs:
                    raise ValueError("input sampling depends on private setting")
        alternate = next(
            item for item in private if item["settings"] == {"assembly": "fewest_cells_first"}
        )
        pair = alternate["episode"]["test"][-1]
        alt_program = ADAPTER.program({"assembly": "fewest_cells_first"})
        canonical_program = ADAPTER.program({"assembly": "query_order"})
        output = evaluator.apply(alt_program, pair["input"])
        counterfactual = evaluator.apply(canonical_program, pair["input"])
        if output == counterfactual:
            raise ValueError("causal counterfactual did not change final output")
        info = PROTOTYPE.intermediate(pair["input"])
        counts = [row["active_cells"] for row in info["query_occurrences"]]
        sorted_counts = [row["active_cells"] for row in info["fewest_first_occurrences"]]
        case = {
            "schema": "35368341e72e-audited-causal-case-v1",
            "task_id": TASK_ID,
            "settings": {"assembly": "fewest_cells_first"},
            "program": alt_program,
            "input": pair["input"],
            "output": output,
            "counterfactual_program": canonical_program,
            "counterfactual_output": counterfactual,
            "intermediate_value": {
                "query_keys": info["query_keys"],
                "active_cell_counts": counts,
                "fewest_first_keys": info["fewest_first_keys"],
                "sorted_active_cell_counts": sorted_counts,
            },
            "ablation": "skip_a",
        }
        report = {
            "schema": "35368341e72e-parametric-authoring-v1",
            "task_id": TASK_ID,
            "settings": [{"assembly": name} for name in ASSEMBLIES],
            "seeds": seeds,
            "demo_counts": demo_counts,
            "queries": 4,
            "matched_inputs_across_settings": True,
            "jobs": rows,
            "racket": evaluator.identity,
            "racket_evaluations": evaluator.evaluations,
            "source_files": [
                {
                    "path": path.name,
                    "sha256": _sha_file(path),
                }
                for path in sorted(
                    [
                        HERE / "adapter.py",
                        HERE / "prototype.py",
                        HERE / "promotion.json",
                        HERE / "canonical.rkt",
                        HERE / "fewest_cells_first.rkt",
                    ]
                )
            ],
            "causal_case_sha256": _sha(case),
            "limits": (
                "Bounded protected-Racket replay over the listed seeds/demo counts and finite rivals; "
                "not universal uniqueness, owner acceptance, or training admission."
            ),
        }
        return report, case
    finally:
        evaluator.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="append", type=int)
    parser.add_argument("--demos", action="append", type=int)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    args = parser.parse_args(argv)
    seeds = args.seed or [0, 17]
    demo_counts = args.demos or [2, 3, 6]
    for seed in seeds:
        if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
            raise ValueError("seed outside 0..2^63-1")
    for demos in demo_counts:
        if type(demos) is not int or not 2 <= demos <= 6:
            raise ValueError("demos outside 2..6")
    report, case = run(seeds, demo_counts)
    _write_new(args.out, report)
    _write_new(args.case, case)
    print(json.dumps({
        "status": "passed",
        "jobs": len(report["jobs"]),
        "racket_evaluations": report["racket_evaluations"],
        "report": str(args.out),
        "case": str(args.case),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
