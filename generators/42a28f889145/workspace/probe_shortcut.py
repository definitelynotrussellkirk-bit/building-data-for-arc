#!/usr/bin/env python3
"""Reproduce the canonical-fitting color-sort shortcut and its counterexample.

This is an authoring probe, not a blind-solve helper. It loads the selected
source by exact task ID, checks every declared canonical shortcut against every
labeled canonical pair, constructs one lawful generated witness, and compares
each rival with an independent connected-component swap oracle.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

# In repository layouts reviewer_support lives under shared/runtime; copied
# runtimes place it at their root. The fallback is source-relative, never cwd.
HERE = Path(__file__).resolve()
for parent in HERE.parents:
    support = parent / "shared" / "runtime"
    if (support / "reviewer_support.py").is_file():
        sys.path.insert(0, str(support))
        break

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "42a28f889145"
SEED = 9
SAMPLE_INDEX = 1
OVERRIDES = {"grid_h": 7, "grid_w": 9, "shape_pair": 0, "color_pair": 0}


def components(grid):
    """Independent same-color four-connected component extraction."""
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append({"color": color, "cells": sorted(cells)})
    return sorted(objects, key=lambda item: min(col for _, col in item["cells"]))


def swap_oracle(grid):
    objects = components(grid)
    if len(objects) != 2:
        raise ValueError(f"expected 2 objects, found {len(objects)}")
    output = deepcopy(grid)
    for row, col in objects[0]["cells"]:
        output[row][col] = objects[1]["color"]
    for row, col in objects[1]["cells"]:
        output[row][col] = objects[0]["color"]
    return output


def differing_cells(left, right):
    return [
        [row, col, left[row][col], right[row][col]]
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--input-out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    canonicals = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    rivals = dict(generator.CANONICAL_SHORTCUTS)
    if not rivals:
        raise RuntimeError("generator declares no canonical shortcuts")

    canonical_results = {}
    for name, rival in rivals.items():
        rows = []
        for pair in canonicals:
            actual = rival(pair["input"])
            rows.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "fits": actual == pair["output"],
                }
            )
        canonical_results[name] = rows

    grid = generator.generate(SEED, SAMPLE_INDEX, **OVERRIDES)
    domain_errors = generator.self_check(grid)
    if domain_errors:
        raise RuntimeError(f"chosen witness is outside generator domain: {domain_errors}")
    intended = swap_oracle(grid)
    objects = components(grid)
    rival_results = {}
    for name, rival in rivals.items():
        rival_output = rival(grid)
        rival_results[name] = {
            "output": rival_output,
            "agrees_with_intended": rival_output == intended,
            "differing_cells": differing_cells(intended, rival_output),
        }

    report = {
        "schema": "42a28f889145-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_hash": generator.RULE_HASH,
        "seed": SEED,
        "sample_index": SAMPLE_INDEX,
        "difficulty": None,
        "overrides": OVERRIDES,
        "domain_errors": domain_errors,
        "observed_overrides": generator.observe_overrides(grid),
        "objects_left_to_right": [
            {"color": item["color"], "cells": item["cells"]} for item in objects
        ],
        "input": grid,
        "intended_output_independent_oracle": intended,
        "canonical_shortcuts": canonical_results,
        "witness_rival_results": rival_results,
        "conclusion": (
            "All declared shortcuts fit every labeled canonical pair, while the "
            "left-color-greater generated witness distinguishes color exchange "
            "from descending color sorting."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.input_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.input_out.write_text(json.dumps({"input": grid}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "input_out": str(args.input_out),
        "generator_sha256": source_sha,
        "canonical_pairs": len(canonicals),
        "rivals": sorted(rivals),
        "all_fit_canonicals": all(
            row["fits"] for rows in canonical_results.values() for row in rows
        ),
        "all_refuted_by_witness": all(
            not row["agrees_with_intended"] for row in rival_results.values()
        ),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
