#!/usr/bin/env python3
"""Pinned one-shot shortcut witness for ticket-488c54aea71c9d5a."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "891a82451a8a"
EXPECTED_SHA256 = "e7ba6890d0edbb7fcf6194dc8e553e6897bbca2773b594e7cd1e1b571afb65a9"
TICKET_ID = "ticket-488c54aea71c9d5a"
PROBE_SEED = "93a9d7385770e3c9049d34d4004d32d608b7976b911d894aeae5403ce5036f3e"
CYCLE = (0, 5, 2, 8, 9, 6, 1, 3, 4)


def _canonical_program(root: Path) -> str:
    matches = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if (
                row.get("task_id") == TASK_ID
                and row.get("content_hash") == TASK_ID
                and row.get("source") == "training"
                and row.get("parent_hash") is None
            ):
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise RuntimeError(f"expected one original canonical program, found {len(matches)}")
    return matches[0]


def _rule_lambda(program: str) -> tuple[str, str]:
    match = re.search(
        r"\(rule!\s+\(lambda\s+\(\s*([A-Za-z_][A-Za-z0-9_?!-]*)\s*\)\s*",
        program,
    )
    if match is None:
        raise ValueError("missing rule! lambda")
    parameter = match.group(1)
    start = match.end()
    while start < len(program) and program[start].isspace():
        start += 1
    depth = 0
    for index in range(start, len(program)):
        if program[index] == "(":
            depth += 1
        elif program[index] == ")":
            depth -= 1
            if depth == 0:
                return parameter, program[start:index + 1]
    raise ValueError("unterminated lambda body")


def _chebyshev(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(cell for row in grid for cell in row)
    background = counts.most_common(1)[0][0]
    seed_cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != background
    ]
    if len(seed_cells) != 1:
        raise ValueError("expected one seed")
    seed_row, seed_col = seed_cells[0]
    start = CYCLE.index(grid[seed_row][seed_col])
    return [
        [
            CYCLE[(start + max(abs(row - seed_row), abs(col - seed_col))) % len(CYCLE)]
            for col in range(len(grid[0]))
        ]
        for row in range(len(grid))
    ]


def run(out: Path) -> dict:
    root = find_root(__file__)
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"source changed: expected {EXPECTED_SHA256}, got {digest}")

    seed = int(PROBE_SEED[:16], 16)
    grid = generator.generate(
        seed,
        0,
        grid_h=5,
        grid_w=5,
        bg_color=7,
        seed_color=5,
        seed_region="corner",
    )
    errors = generator.self_check(grid)
    if errors:
        raise AssertionError(f"generated witness is unlawful: {errors}")

    program = _canonical_program(root)
    parameter, body = _rule_lambda(program)
    bridge = RacketBridge()
    try:
        runtime = bridge.runtime_identity
        bridge.define_grid(parameter, grid)
        intended = bridge.eval_text(body)
    finally:
        bridge.shutdown()
    mirror = generator.rule_mirror(grid)
    shortcut = _chebyshev(grid)
    if intended != mirror:
        raise AssertionError("canonical Racket and selected mirror disagree")

    differing = [
        {"row": row, "col": col, "intended": intended[row][col], "shortcut": shortcut[row][col]}
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if intended[row][col] != shortcut[row][col]
    ]
    if not differing:
        raise AssertionError("Chebyshev shortcut was not refuted")

    result = {
        "schema": "arcpuzzles-adversarial-witness-ticket-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "probe_seed": PROBE_SEED,
        "source": {
            "path": str(source.relative_to(root)),
            "sha256": digest,
            "version": generator.VERSION,
            "rule_hash": generator.RULE_HASH,
        },
        "shortcut": "Use Chebyshev distance rings instead of Manhattan distance rings.",
        "lawful_input": grid,
        "self_check_errors": errors,
        "canonical_racket_output": intended,
        "shortcut_output": shortcut,
        "differing_cell_count": len(differing),
        "first_difference": differing[0],
        "racket_runtime": runtime,
        "outcome": (
            "completed: retained a lawful protected-Racket witness; this shortcut is "
            "already declared by the selected generator, so it is not a new safety finding"
        ),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out.resolve())
    print(json.dumps({
        "ticket_id": result["ticket_id"],
        "task_id": result["task_id"],
        "differing_cell_count": result["differing_cell_count"],
        "first_difference": result["first_difference"],
        "outcome": result["outcome"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
