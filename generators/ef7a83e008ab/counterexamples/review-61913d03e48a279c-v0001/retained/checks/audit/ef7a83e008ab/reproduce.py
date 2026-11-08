#!/usr/bin/env python3
"""Reproduce the count-all-foreground teaching shortcut on selected bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "ef7a83e008ab"
SEED = 0
SAMPLE_INDICES = (9, 10, 11, 12)
DIFFICULTY = "medium"


def components(grid, predicate):
    h, w = len(grid), len(grid[0])
    seen = set()
    total = 0
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or not predicate(grid[r][c]):
                continue
            total += 1
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and predicate(grid[nr][nc])
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return total


def bar(n):
    return [[8 if i % 2 == 0 else 4 for i in range(n)]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    grids = [
        generator.generate(SEED, index, difficulty=DIFFICULTY)
        for index in SAMPLE_INDICES
    ]
    red_counts = [components(grid, lambda value: value == 2) for grid in grids]
    foreground_counts = [components(grid, lambda value: value != 0) for grid in grids]
    validator_errors = [
        generator.self_check(grid, difficulty=DIFFICULTY) for grid in grids
    ]
    intended = [bar(count) for count in red_counts]
    rival = [bar(count) for count in foreground_counts]
    distractor_colors = [
        sorted({value for row in grid for value in row if value not in (0, 2)})
        for grid in grids
    ]
    payload = {
        "schema": "ef7a83e008ab-current-source-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "generation": {
            "seed": SEED,
            "sample_indices": list(SAMPLE_INDICES),
            "difficulty": DIFFICULTY,
            "overrides": {},
        },
        "lesson_policy": {
            "demonstrations": [0, 1, 2],
            "query": 3,
            "ordered_consecutive_samples": True,
        },
        "red_component_counts": red_counts,
        "all_foreground_component_counts": foreground_counts,
        "distractor_colors": distractor_colors,
        "validator_errors": validator_errors,
        "python_intended_outputs": intended,
        "rival": "count_all_foreground_components",
        "rival_outputs": rival,
        "demo_rival_fits_python": [rival[i] == intended[i] for i in range(3)],
        "query_rival_differs_python": rival[3] != intended[3],
        "input_sha256": [
            hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            for grid in grids
        ],
    }
    (out / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
    (out / "probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha,
        "red_counts": red_counts,
        "foreground_counts": foreground_counts,
        "demo_rival_fits": payload["demo_rival_fits_python"],
        "query_rival_differs": payload["query_rival_differs_python"],
        "validator_errors": validator_errors,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
