#!/usr/bin/env python3
"""Find and replay a lesson where an ignore-portals rival survives demos."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "4cea2727fcf9"
SEED = 22
DIFFICULTY = "medium"
N_DEMOS = 5


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def grid_sha256(value) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def canonical_program(root: Path) -> str:
    rows = []
    with canonical_path(root).open() as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(str(row["program_solution"]))
    unique = list(dict.fromkeys(rows))
    if len(unique) != 1:
        raise RuntimeError(f"expected one canonical program, found {len(unique)}")
    return unique[0]


def replace_balanced_form(source: str, marker: str, replacement: str) -> str:
    start = source.find(marker)
    if start < 0:
        raise RuntimeError(f"missing marker {marker!r}")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[:start] + replacement + source[index + 1 :]
    raise RuntimeError("unbalanced portal-exit definition")


def ignore_portals_program(source: str) -> str:
    return replace_balanced_form(
        source,
        "(define (portal-exit p)",
        "(define (portal-exit p) p)",
    )


def racket_datum(grid) -> str:
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def execute(bridge: RacketBridge, source: str, grid):
    body = strip_rule_wrapper(source)
    bridge.define_grid("g", grid)
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    return normalize_grid(bridge.eval_text(expression))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_program(root)
    rival = ignore_portals_program(canonical)
    if canonical == rival:
        raise RuntimeError("rival source did not change")

    grids = [
        generator.generate(SEED, index, difficulty=DIFFICULTY)
        for index in range(N_DEMOS + 1)
    ]
    for index, grid in enumerate(grids):
        errors = generator.self_check(grid, difficulty=DIFFICULTY)
        if errors:
            raise RuntimeError(f"generated pair {index} invalid: {errors}")

    rows = []
    with RacketBridge() as bridge:
        runtime = bridge.runtime_identity
        for index, grid in enumerate(grids):
            intended = execute(bridge, canonical, grid)
            alternative = execute(bridge, rival, grid)
            rows.append(
                {
                    "role": "demo" if index < N_DEMOS else "query",
                    "sample_index": index,
                    "input": grid,
                    "input_sha256": grid_sha256(grid),
                    "portal_cells": sum(value == 4 for row in grid for value in row),
                    "canonical_output": intended,
                    "ignore_portals_output": alternative,
                    "outputs_equal": intended == alternative,
                }
            )

    report = {
        "schema": "audit-4cea2727fcf9-ignore-portals-rival-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "n_demos": N_DEMOS,
        "canonical_program_sha256": sha256_text(canonical),
        "ignore_portals_program_sha256": sha256_text(rival),
        "rival_source_change": (
            "Replace the canonical portal-exit definition with identity: "
            "(define (portal-exit p) p)."
        ),
        "runtime": runtime,
        "pairs": rows,
        "rival_fits_every_demo": all(row["outputs_equal"] for row in rows[:N_DEMOS]),
        "rival_disagrees_on_query": not rows[N_DEMOS]["outputs_equal"],
        "finding": (
            "For seed 22 and sample indices 0..5, the first five emitted pairs "
            "do not distinguish the canonical portal rule from ignoring portals, "
            "but the sixth pair does. A five-demo lesson can therefore leave a "
            "canonical-fitting rival alive exactly when the query needs portals."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "rival_fits_every_demo": report["rival_fits_every_demo"],
                "rival_disagrees_on_query": report["rival_disagrees_on_query"],
            },
            sort_keys=True,
        )
    )
    return int(
        not report["rival_fits_every_demo"]
        or not report["rival_disagrees_on_query"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
