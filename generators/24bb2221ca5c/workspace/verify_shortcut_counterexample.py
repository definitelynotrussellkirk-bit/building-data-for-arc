#!/usr/bin/env python3
"""Verify one exact bbox-fill shortcut counterexample against real Racket."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys


TASK_HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "shortcut_counterexample_generator", TASK_HOME / "generator.py"
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
            if row.get("task_id") == task_id:
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
    grid = [[0] * 12 for _ in range(8)]
    # Closed 5x5 color-3 frame.
    for col in range(1, 6):
        grid[1][col] = 3
        grid[5][col] = 3
    for row in range(1, 6):
        grid[row][1] = 3
        grid[row][5] = 3
    # Open 5x4 color-8 near-miss, with a non-corner gap at (4, 8).
    for col in range(8, 12):
        grid[2][col] = 8
        grid[6][col] = 8
    for row in range(2, 7):
        grid[row][8] = 8
        grid[row][11] = 8
    grid[4][8] = 0
    return grid


def build_evidence() -> dict:
    gen = _load_generator()
    grid = counterexample_input()
    errors = gen.self_check(grid)
    if errors:
        raise RuntimeError(f"counterexample outside generator grammar: {errors}")

    python_intended = gen.rule_mirror(grid)
    rival = gen.SEMANTIC_RIVALS["fill_every_component_bbox"](grid)
    rule_source, rule_label = _load_canonical_rule(gen.TASK_ID)
    racket_output = _apply_racket(rule_source, grid)

    differing_cells = [
        {
            "row": row,
            "col": col,
            "intended": python_intended[row][col],
            "rival": rival[row][col],
        }
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if python_intended[row][col] != rival[row][col]
    ]
    evidence = {
        "schema": "arc-shortcut-counterexample-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "rival": "fill_every_component_bbox",
        "rule_source": rule_label,
        "input": grid,
        "racket_output": racket_output,
        "python_mirror_output": python_intended,
        "rival_output": rival,
        "racket_matches_python_mirror": racket_output == python_intended,
        "rival_disagrees": rival != python_intended,
        "differing_cells": differing_cells,
        "generator_emits_witness": any(
            (lambda generated: (
                gen.SEMANTIC_WITNESSES["open_gap_decoy_stays_zero"](generated)
                and gen.SEMANTIC_RIVALS["fill_every_component_bbox"](generated)
                != gen.rule_mirror(generated)
            ))(gen.generate(2400, sample_index, difficulty="hard"))
            for sample_index in range(gen.EXAMPLES_NEEDED)
        ),
    }
    if not evidence["racket_matches_python_mirror"]:
        raise RuntimeError("Python mirror disagrees with selected Racket authority")
    if not evidence["rival_disagrees"]:
        raise RuntimeError("counterexample does not refute bbox-fill rival")
    if not evidence["generator_emits_witness"]:
        raise RuntimeError("scheduled generator window did not emit bbox-fill witness")
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    evidence = build_evidence()
    text = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(
            f"verified {len(evidence['differing_cells'])} disagreement cells; "
            f"wrote {args.output}"
        )
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
