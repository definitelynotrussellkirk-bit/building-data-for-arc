#!/usr/bin/env python3
"""Run the bounded source-bound audit for b5b012cd97d9's native family."""
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
TASK_ID = "b5b012cd97d9"


def _load_family():
    path = HERE / "family.py"
    name = "_audit_b5b012cd97d9_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


family = _load_family()


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest_file(path: Path) -> str:
    return _digest_bytes(path.read_bytes())


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


class ProtectedExecutor:
    def __init__(self):
        self.bridge = RacketBridge()
        identity = dict(self.bridge.runtime_identity)
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError(f"protected Racket required, got {identity}")
        self.identity = identity
        self._wrapped: dict[str, str] = {}
        self.evaluations = 0

    def apply(self, program: str, grid: list[list[int]]) -> list[list[int]]:
        wrapped = self._wrapped.setdefault(program, wrap_rule(program))
        value = self.bridge.eval_text(f"({wrapped} {_grid_literal(grid)})")
        self.evaluations += 1
        if (
            type(value) is not list
            or not value
            or type(value[0]) is not list
            or not value[0]
            or any(
                type(row) is not list
                or len(row) != len(value[0])
                or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                for row in value
            )
        ):
            raise RuntimeError("Racket returned a non-grid")
        return value

    def close(self):
        self.bridge.close()


def _shape(grid: list[list[int]]) -> list[int]:
    return [len(grid), len(grid[0])]


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_seeds(raw: str) -> list[int]:
    values = [int(item) for item in raw.split(",") if item.strip()]
    if len(values) != len(set(values)) or not values or any(value < 0 for value in values):
        raise argparse.ArgumentTypeError("seeds must be distinct nonnegative comma-separated integers")
    return values


def _analysis_summary(grid: list[list[int]]) -> dict[str, Any]:
    info = family.analyze(grid)
    return {
        "input_shape": _shape(grid),
        "background": info["background"],
        "background_count": info["background_count"],
        "big": {"color": info["big"]["color"], "count": info["big"]["count"]},
        "big_side_intermediate": info["big_side"],
        "canonical_secondary": {
            "color": info["canonical_secondary"]["color"],
            "count": info["canonical_secondary"]["count"],
        },
        "relay_secondary": {"color": info["relay"]["color"], "count": info["relay"]["count"]},
        "secondary_counts": sorted(record["count"] for record in info["secondary_candidates"]),
        "role_count": info["role_count"],
    }


def run(output: Path, seeds: list[int], sweep: int) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.mkdir(parents=True)

    executor = ProtectedExecutor()
    protected_cases = []
    public_rows = []
    try:
        programs = {
            setting: family.program({"secondary": setting})
            for setting in family.SECONDARY_SETTINGS
        }
        for seed in seeds:
            for setting in family.SECONDARY_SETTINGS:
                episode = family.generate(seed, {"secondary": setting}, 3, 4)
                pairs = episode["train"] + episode["test"]
                actual = [executor.apply(programs[setting], pair["input"]) for pair in pairs]
                if actual != [pair["output"] for pair in pairs]:
                    raise AssertionError(f"protected labels differ for seed={seed} setting={setting}")
                other = next(value for value in family.SECONDARY_SETTINGS if value != setting)
                other_demo = [executor.apply(programs[other], pair["input"]) for pair in episode["train"]]
                if all(value == pair["output"] for value, pair in zip(other_demo, episode["train"])):
                    raise AssertionError(f"declared rival survived seed={seed} setting={setting}")
                protected_cases.append({
                    "seed": seed,
                    "setting": setting,
                    "pair_count": len(pairs),
                    "demo_count": 3,
                    "query_count": 4,
                    "program_sha256": _digest_bytes(programs[setting].encode("utf-8")),
                    "other_setting_rejected": other,
                    "input_shapes": [_shape(pair["input"]) for pair in pairs],
                    "output_shapes": [_shape(pair["output"]) for pair in pairs],
                    "teaching": family.teaching_report([pair["input"] for pair in episode["train"][:2]]),
                })

                short = family.generate(seed, {"secondary": setting}, 3, 1)
                first = family.public_turn(episode, 0)
                if first != family.public_turn(short, 0):
                    raise AssertionError("first public turn is not query-prefix stable")
                raw = public_challenge_bytes(first)
                identifier = public_challenge_id(first)
                if identifier != _digest_bytes(raw):
                    raise AssertionError("public identifier does not hash exact visible bytes")
                text = raw.decode("utf-8")
                if setting in text or "program_solution" in text or "settings" in text:
                    raise AssertionError("private metadata leaked into public turn")
                public_rows.append({
                    "seed": seed,
                    "setting": setting,
                    "public_id": identifier,
                    "bytes": len(raw),
                    "query_shape": _shape(episode["test"][0]["input"]),
                    "future_queries_hidden": len(episode["test"]) - len(first["test"]),
                })

        witness = family.sequential_witness_input()
        correct_program = programs["big_side_relay"]
        wrong_program = (HERE / "fixed_four_relay.rkt").read_text(encoding="utf-8")
        correct = executor.apply(correct_program, witness)
        wrong = executor.apply(wrong_program, witness)
        if correct == wrong:
            raise AssertionError("wrong-intermediate counterfactual did not change final output")
        witness_record = {
            "schema": "arcpuzzles-sequential-witness-v1",
            "task_id": TASK_ID,
            "setting": {"secondary": "big_side_relay"},
            "step_a": "Count non-background colors, select the unique largest mass, and derive its integer square side.",
            "intermediate": _analysis_summary(witness)["big_side_intermediate"],
            "step_b": "Select the unique remaining color whose count equals that derived side, then pack its square beside the largest square.",
            "why_b_depends_on_a": "The secondary target count is not fixed and is unavailable until the largest mass has been selected and square-rooted.",
            "counterfactual": "Use the wrong fixed intermediate 4 instead of the derived side 9.",
            "input": witness,
            "analysis": _analysis_summary(witness),
            "correct_program": "big_side_relay.rkt",
            "correct_program_sha256": _digest_bytes(correct_program.encode("utf-8")),
            "counterfactual_program": "fixed_four_relay.rkt",
            "counterfactual_program_sha256": _digest_bytes(wrong_program.encode("utf-8")),
            "correct_output": correct,
            "counterfactual_output": wrong,
            "correct_output_shape": _shape(correct),
            "counterfactual_output_shape": _shape(wrong),
            "outputs_differ": True,
            "protected_racket": True,
        }
        _write(output / "sequential-witness.json", witness_record)
    finally:
        runtime_identity = executor.identity
        protected_evaluations = executor.evaluations
        executor.close()

    sweep_failures = []
    episodes = 0
    labeled_pairs = 0
    settings_seen = {setting: 0 for setting in family.SECONDARY_SETTINGS}
    shapes = set()
    for seed in range(sweep):
        full_inputs = family.sample_inputs(seed, demos=6, queries=4)
        teaching = family.teaching_report(full_inputs[:2])
        expected = {setting: [setting] for setting in family.SECONDARY_SETTINGS}
        if teaching["survivors"] != expected:
            sweep_failures.append({"seed": seed, "kind": "teaching", "report": teaching})
        for demos in (2, 3, 6):
            for setting in family.SECONDARY_SETTINGS:
                episode = family.generate(seed, {"secondary": setting}, demos, 4)
                episodes += 1
                settings_seen[setting] += 1
                pairs = episode["train"] + episode["test"]
                labeled_pairs += len(pairs)
                identities = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
                if len(identities) != len(set(identities)):
                    sweep_failures.append({"seed": seed, "setting": setting, "demos": demos, "kind": "duplicate"})
                for pair in pairs:
                    shapes.add(tuple(_shape(pair["input"])))
                    if pair["output"] != family.solve_python(pair["input"], setting):
                        sweep_failures.append({"seed": seed, "setting": setting, "demos": demos, "kind": "claim"})
    if sweep_failures:
        raise AssertionError(f"bounded sweep failures: {sweep_failures[:3]}")

    stress = family.generate(0, {"secondary": "big_side_relay"}, 3, 4)["test"][-1]["input"]
    stress_info = family.analyze(stress)
    stress_non_background = sum(
        cell != stress_info["background"] for row in stress for cell in row
    )
    boundary = {
        "top": any(cell != stress_info["background"] for cell in stress[0]),
        "bottom": any(cell != stress_info["background"] for cell in stress[-1]),
        "left": any(row[0] != stress_info["background"] for row in stress),
        "right": any(row[-1] != stress_info["background"] for row in stress),
    }
    if not all(boundary.values()) or stress_non_background < 400:
        raise AssertionError("30x30 stress query is not substantive on every boundary")

    source_files = [
        "adapter.py",
        "family.py",
        "promotion.json",
        "canonical.rkt",
        "big_side_relay.rkt",
        "fixed_four_relay.rkt",
        "audit.py",
    ]
    source_hashes = {name: _digest_file(HERE / name) for name in source_files}
    self_audit = {
        "schema": "b5b012cd97d9-bounded-self-audit-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "settings": list(family.SECONDARY_SETTINGS),
        "protected_racket": {
            "runtime": runtime_identity,
            "evaluations": protected_evaluations,
            "cases": protected_cases,
        },
        "finite_rivals": list(family.RIVAL_POLICIES),
        "sweep": {
            "seeds": sweep,
            "demo_counts": [2, 3, 6],
            "queries": 4,
            "episodes": episodes,
            "labeled_pairs": labeled_pairs,
            "settings_seen": settings_seen,
            "input_shapes": [list(shape) for shape in sorted(shapes)],
            "failures": [],
        },
        "stress_30x30": {
            "shape": _shape(stress),
            "non_background_cells": stress_non_background,
            "role_count": stress_info["role_count"],
            "boundary_content": boundary,
        },
        "source_sha256": source_hashes,
        "limits": "Finite rivals, seeds, counts, and protected executions only; no universal identifiability or measured training benefit.",
        "training_admitted": False,
    }
    public_check = {
        "schema": "b5b012cd97d9-public-projection-check-v1",
        "status": "passed",
        "rows": public_rows,
        "contract": "Each record exposes demonstrations and exactly one current query input; settings, programs, answers, future inputs, and total query count remain private.",
    }
    _write(output / "self-audit.json", self_audit)
    _write(output / "public-check.json", public_check)
    index = {
        "schema": "b5b012cd97d9-parametric-evidence-index-v1",
        "status": "passed",
        "files": {
            name: _digest_file(output / name)
            for name in ("self-audit.json", "public-check.json", "sequential-witness.json")
        },
    }
    _write(output / "index.json", index)
    return {
        "status": "passed",
        "out": str(output),
        "protected_racket_evaluations": protected_evaluations,
        "sweep_episodes": episodes,
        "sweep_labeled_pairs": labeled_pairs,
        "sequential_outputs_differ": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=_parse_seeds, default=[0, 17])
    parser.add_argument("--sweep", type=int, default=64)
    args = parser.parse_args()
    if not 1 <= args.sweep <= 512:
        parser.error("--sweep must be in 1..512")
    print(json.dumps(run(args.out, args.seeds, args.sweep), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
