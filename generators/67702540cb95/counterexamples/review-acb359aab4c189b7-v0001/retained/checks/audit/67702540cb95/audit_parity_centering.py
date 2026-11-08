#!/usr/bin/env python3
"""Find generated shapes that the exact-centering Racket rule erases."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator, normalize_grid

TASK_ID = "67702540cb95"


def blue_count(grid):
    return sum(value == 1 for row in grid for value in row)


def partition_ranges(lines, size):
    ranges = []
    start = 0
    for line in sorted(lines):
        if start <= line - 1:
            ranges.append((start, line - 1))
        start = line + 1
    if start <= size - 1:
        ranges.append((start, size - 1))
    return ranges


def incompatible_cells(grid):
    h, w = len(grid), len(grid[0])
    reds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    row_ranges = partition_ranges({r for r, _ in reds}, h)
    col_ranges = partition_ranges({c for _, c in reds}, w)
    result = []
    for r0, r1 in row_ranges:
        for c0, c1 in col_ranges:
            blue = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if grid[r][c] == 1]
            if not blue:
                continue
            sh = max(r for r, _ in blue) - min(r for r, _ in blue) + 1
            sw = max(c for _, c in blue) - min(c for _, c in blue) + 1
            ch, cw = r1 - r0 + 1, c1 - c0 + 1
            if (ch - sh) % 2 or (cw - sw) % 2:
                result.append({
                    "cell_range": [r0, r1, c0, c1],
                    "cell_shape": [ch, cw],
                    "blue_bbox_shape": [sh, sw],
                    "row_shift_is_fractional": bool((ch - sh) % 2),
                    "col_shift_is_fractional": bool((cw - sw) % 2),
                    "blue_cells": blue,
                })
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-seeds", type=int, default=40)
    args = parser.parse_args(argv)
    root = find_root(__file__)
    generator, source, generator_sha = load_selected_generator(TASK_ID, root=root)
    catalog = Catalog(root)

    rows = []
    grids = []
    for band in ("easy", "medium", "hard"):
        for seed in range(args.max_seeds):
            grid = normalize_grid(generator.generate(seed, 0, difficulty=band))
            grids.append(grid)
            rows.append({
                "difficulty": band,
                "seed": seed,
                "sample_index": 0,
                "input": grid,
                "input_blue_count": blue_count(grid),
                "incompatible_cells": incompatible_cells(grid),
                "self_check": generator.self_check(grid, difficulty=band),
            })

    # Apply in public-API batches.
    identities = []
    for offset in range(0, len(grids), 64):
        applied = catalog.apply(TASK_ID, grids[offset:offset + 64], timeout=180)
        identities.append({
            key: applied.get(key)
            for key in ("generator_sha256", "executed_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog")
        })
        for row, result in zip(rows[offset:offset + 64], applied["results"], strict=True):
            row["output"] = result["output"]
            row["output_blue_count"] = blue_count(result["output"])
            row["blue_count_delta"] = row["output_blue_count"] - row["input_blue_count"]
            row["shape_erasure"] = row["output_blue_count"] < row["input_blue_count"]

    affected = [row for row in rows if row["shape_erasure"]]
    if not affected:
        raise AssertionError("finite search did not reproduce shape erasure")
    witness = affected[0]
    if witness["self_check"]:
        raise AssertionError("selected witness was rejected by self_check")
    if not witness["incompatible_cells"]:
        raise AssertionError("shape erasure witness has no parity-incompatible cell")

    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK_ID,
        "finding": "generator emits parity-incompatible shape/cell sizes; exact Racket half-cell shifts erase blue shapes",
        "classification": "reproduced_generated_input_defect",
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": generator_sha,
        "generator_version": generator.VERSION,
        "command": [sys.executable, *sys.argv],
        "cwd": str(Path.cwd()),
        "search": {
            "bands": ["easy", "medium", "hard"],
            "seed_start": 0,
            "seed_stop_exclusive": args.max_seeds,
            "sample_index": 0,
            "inputs": len(rows),
            "affected_inputs": len(affected),
        },
        "reference_identities": identities,
        "witness": witness,
        "root_cause": (
            "_bands chooses cell sizes 3..6 and generate chooses rectangle sizes 1..3 independently. "
            "The Racket rule uses (/ (- cell-size shape-size) 2); an odd difference is a rational half-cell shift, "
            "so no integer output coordinate matches and those blue pixels disappear."
        ),
        "limitations": [
            "Finite search over sample_index 0 only.",
            "This audit does not propose or apply a repair.",
        ],
        "all_rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "out": str(args.out), "inputs": len(rows), "affected": len(affected),
        "first": {key: witness[key] for key in ("difficulty", "seed", "sample_index", "input_blue_count", "output_blue_count")},
        "generator_sha256": generator_sha,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
