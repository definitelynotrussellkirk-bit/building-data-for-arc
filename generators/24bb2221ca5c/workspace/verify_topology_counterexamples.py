#!/usr/bin/env python3
"""Verify multi-hole and same-color-component counterexamples against Racket.

The canonical examples contain one hole per component and one component per
color.  This tool materializes one compact lawful grid that violates both
accidental regularities, runs the selected canonical Racket rule, and compares
it with the generator mirror and two executable shortcut rules.
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


RIVALS = ("fill_one_hole_per_component", "merge_same_color_bboxes")


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "topology_counterexample_generator", TASK_HOME / "generator.py"
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


def counterexample_input() -> list[list[int]]:
    """Return one two-hole component plus a disconnected same-color ring."""
    grid = [[0] * 14 for _ in range(8)]

    # A two-chamber 5x7 ring with a central divider and one outward spur.
    for col in range(1, 8):
        grid[1][col] = 1
        grid[5][col] = 1
    for row in range(1, 6):
        grid[row][1] = 1
        grid[row][4] = 1
        grid[row][7] = 1
    grid[3][8] = 1

    # A second disconnected ring in the same color, separated by a blank moat.
    for col in range(10, 14):
        grid[1][col] = 1
        grid[5][col] = 1
    for row in range(1, 6):
        grid[row][10] = 1
        grid[row][13] = 1
    return grid


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
    grid = counterexample_input()
    errors = gen.self_check(grid)
    if errors:
        raise RuntimeError(f"counterexample outside generator grammar: {errors}")

    python_intended = gen.rule_mirror(grid)
    rule_source, rule_label = _load_canonical_rule(gen.TASK_ID)
    racket_output = _apply_racket(rule_source, grid)
    if racket_output != python_intended:
        raise RuntimeError("Python mirror disagrees with selected Racket authority")

    cases: dict[str, Any] = {}
    for rival_name in RIVALS:
        rival_output = gen.SEMANTIC_RIVALS[rival_name](grid)
        differences = _differences(python_intended, rival_output)
        if not differences:
            raise RuntimeError(f"counterexample does not refute {rival_name}")
        cases[rival_name] = {
            "rival_output": rival_output,
            "differing_cells": differences,
            "disagreement_count": len(differences),
        }

    generated = [
        gen.generate(2400, sample_index, difficulty="hard")
        for sample_index in range(gen.EXAMPLES_NEEDED)
    ]
    generated_witnesses = {
        "component_may_have_multiple_holes": any(
            gen.SEMANTIC_WITNESSES["component_may_have_multiple_holes"](item)
            for item in generated
        ),
        "same_color_components_stay_separate": any(
            gen.SEMANTIC_WITNESSES["same_color_components_stay_separate"](item)
            for item in generated
        ),
    }
    if not all(generated_witnesses.values()):
        raise RuntimeError("scheduled lesson did not emit both topology witnesses")

    return {
        "schema": "arc-topology-counterexamples-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "rule_source": rule_label,
        "input": grid,
        "racket_output": racket_output,
        "python_mirror_output": python_intended,
        "racket_matches_python_mirror": True,
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
