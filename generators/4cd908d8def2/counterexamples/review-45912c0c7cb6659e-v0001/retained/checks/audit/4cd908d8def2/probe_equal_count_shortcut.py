#!/usr/bin/env python3
"""Reproduce the equal-foreground-count shortcut in 4cd908d8def2."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "4cd908d8def2"


def split_panels(grid):
    h, w = len(grid), len(grid[0])
    seps = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    starts = [0, *(c + 1 for c in seps)]
    ends = [*seps, w]
    return [[row[start:end] for row in grid] for start, end in zip(starts, ends)]


def nonzero_count(panel):
    return sum(value != 0 for row in panel for value in row)


def count_shortcut(grid):
    panels = split_panels(grid)
    target = nonzero_count(panels[0])
    return next(panel for panel in panels[1:] if nonzero_count(panel) == target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    rows = []
    inputs = []
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(20):
            grid = gen.generate(20261019, sample_index, difficulty=difficulty)
            panels = split_panels(grid)
            counts = [nonzero_count(panel) for panel in panels]
            matches = [i for i, count in enumerate(counts[1:], 1) if count == counts[0]]
            shortcut = count_shortcut(grid)
            rows.append({
                "difficulty": difficulty,
                "sample_index": sample_index,
                "shape": [len(grid), len(grid[0])],
                "panel_counts": counts,
                "equal_count_candidate_indices": matches,
                "self_check_errors": gen.self_check(grid),
                "shortcut_output": shortcut,
            })
            inputs.append(grid)
    args.inputs.write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
    args.manifest.write_text(json.dumps({
        "task_id": TASK_ID,
        "generator_source": str(source),
        "generator_sha256": digest,
        "seed": 20261019,
        "cases": rows,
        "summary": {
            "cases": len(rows),
            "all_have_exactly_one_equal_count_candidate": all(
                len(row["equal_count_candidate_indices"]) == 1 for row in rows
            ),
            "all_self_check_valid": all(not row["self_check_errors"] for row in rows),
        },
    }, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
