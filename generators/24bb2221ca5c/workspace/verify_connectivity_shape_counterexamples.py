#!/usr/bin/env python3
"""Verify 4-connectivity and nonrectangular-cavity teaching controls.

The official examples use complete rectangular frames, so they do not decide
whether background reachability is 4- or 8-connected and they never require a
nonrectangular hole to fill.  This tool checks one exact counterexample for
each ambiguity against the selected canonical Racket program, the Python
mirror, and the corresponding executable rival.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


TASK_HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402


CASE_RIVALS = {
    "corner_gap": "eight_connected_holes",
    "nonrectangular_cavity": "rectangular_holes_only",
}


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "connectivity_shape_counterexample_generator", TASK_HOME / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load selected generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_canonical_rule(task_id: str) -> tuple[str, str]:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            source = row.get("program_solution")
            if not isinstance(source, str) or not source.strip():
                raise RuntimeError(f"canonical row {task_id} has no program_solution")
            return source, "shared/data/canonical/puzzles.jsonl#program_solution"
    raise RuntimeError(f"canonical row {task_id} not found")


def _apply_racket(rule_source: str, grid: list[list[int]]) -> list[list[int]]:
    source = rule_source.strip()
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise RuntimeError("counterexample verifier expects canonical (rule! BODY) form")
    callable_source = f"(lambda (g) {source[len(prefix):-1]})"
    bridge = RacketBridge()
    try:
        bridge.eval_text(f"(define __review_rule {callable_source})")
        bridge.define_grid("__review_input", grid)
        return bridge.eval_text("(__review_rule __review_input)")
    finally:
        bridge.shutdown()


def _corner_gap_input() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(8)]
    for col in range(2, 7):
        grid[1][col] = 8
        grid[5][col] = 8
    for row in range(1, 6):
        grid[row][2] = 8
        grid[row][6] = 8
    grid[1][2] = 0
    return grid


def _nonrectangular_cavity_input() -> list[list[int]]:
    grid = [[0] * 12 for _ in range(8)]
    for row in range(1, 5):
        for col in range(1, 6):
            grid[row][col] = 1
    for row, col in ((2, 2), (2, 4), (3, 3), (3, 4)):
        grid[row][col] = 0
    grid[2][6] = 1

    for col in range(8, 12):
        grid[1][col] = 1
        grid[4][col] = 1
    for row in range(1, 5):
        grid[row][8] = 1
        grid[row][11] = 1
    return grid


def counterexample_inputs() -> dict[str, list[list[int]]]:
    return {
        "corner_gap": _corner_gap_input(),
        "nonrectangular_cavity": _nonrectangular_cavity_input(),
    }


def _differences(
    intended: list[list[int]], rival: list[list[int]]
) -> list[dict[str, int]]:
    return [
        {
            "row": row,
            "col": col,
            "intended": intended[row][col],
            "rival": rival[row][col],
        }
        for row in range(len(intended))
        for col in range(len(intended[0]))
        if intended[row][col] != rival[row][col]
    ]


def build_evidence() -> dict[str, Any]:
    gen = _load_generator()
    rule_source, rule_label = _load_canonical_rule(gen.TASK_ID)
    cases: dict[str, Any] = {}

    for case_name, grid in counterexample_inputs().items():
        errors = gen.self_check(grid)
        if errors:
            raise RuntimeError(f"{case_name} outside generator grammar: {errors}")
        python_intended = gen.rule_mirror(grid)
        racket_output = _apply_racket(rule_source, grid)
        if racket_output != python_intended:
            raise RuntimeError(f"Racket/Python disagreement for {case_name}")

        rival_name = CASE_RIVALS[case_name]
        rival_output = gen.SEMANTIC_RIVALS[rival_name](grid)
        differences = _differences(python_intended, rival_output)
        if not differences:
            raise RuntimeError(f"{case_name} does not refute {rival_name}")
        cases[case_name] = {
            "input": grid,
            "racket_output": racket_output,
            "python_mirror_output": python_intended,
            "racket_matches_python_mirror": True,
            "rival": rival_name,
            "rival_output": rival_output,
            "differing_cells": differences,
            "disagreement_count": len(differences),
        }

    generated = [
        gen.generate(2718, sample_index, difficulty="hard")
        for sample_index in range(gen.EXAMPLES_NEEDED)
    ]
    generated_witnesses = {
        witness: any(gen.SEMANTIC_WITNESSES[witness](grid) for grid in generated)
        for witness in ("corner_gap_still_encloses", "nonrectangular_hole_fills")
    }
    if not all(generated_witnesses.values()):
        raise RuntimeError("scheduled lesson did not emit both new witnesses")

    return {
        "schema": "arc-connectivity-shape-counterexamples-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "rule_source": rule_label,
        "cases": cases,
        "generated_witnesses": generated_witnesses,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    evidence = build_evidence()
    text = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        counts = {
            name: case["disagreement_count"]
            for name, case in evidence["cases"].items()
        }
        print(f"verified {counts}; wrote {args.output}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
