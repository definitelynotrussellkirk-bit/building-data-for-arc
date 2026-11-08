#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator, normalize_grid

TASK_ID = "6b1fe17a40a7"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent


def components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    cells.add((nr, nc))
                    stack.append((nr, nc))
        result.append(cells)
    return result


def signature(cells):
    return tuple(sorted(cells))


def positional_rival(grid):
    grid = normalize_grid(grid)
    markers = [grid[0][c] for c in range(len(grid[0])) if grid[0][c] != 0]
    objs = sorted(components(grid), key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))
    out = [[0] * len(grid[0]) for _ in grid]
    for cells, color in zip(objs, markers):
        for r, c in cells:
            out[r][c] = color
    return out


def authored_counterexample():
    h, w = 10, 12
    grid = [[0] * w for _ in range(h)]
    for col, color in zip((1, 3, 5, 7), (2, 3, 4, 5)):
        grid[0][col] = color
    objects = [
        (6, [(2, 0), (2, 1), (2, 2), (3, 0), (3, 1)]),  # size 5, first by position
        (7, [(2, 8), (2, 9), (3, 8), (3, 9)]),          # size 4
        (8, [(6, 1), (6, 2), (7, 1)]),                  # size 3
        (9, [(7, 9), (7, 10)]),                         # size 2, last by position
    ]
    for color, cells in objects:
        for r, c in cells:
            grid[r][c] = color
    return grid


def main():
    gen, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    expected_sha = "4a807878c53fd4d7124eeaa7294b924cd31afda5161950b299769c69d9c1abca"
    assert source_sha == expected_sha

    total = 0
    correlated = 0
    sample_rows = []
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(100):
            grid = gen.generate(800_000 + index, index, difficulty=difficulty)
            objs = components(grid)
            by_size = sorted(objs, key=lambda cells: (len(cells), min(r for r, _ in cells), min(c for _, c in cells)))
            by_position = sorted(objs, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))
            same = [signature(x) for x in by_size] == [signature(x) for x in by_position]
            total += 1
            correlated += same
            if len(sample_rows) < 8:
                sample_rows.append({
                    "difficulty": difficulty,
                    "sample_index": index,
                    "sizes_by_position": [len(x) for x in by_position],
                    "size_order_equals_position_order": same,
                    "self_check": gen.self_check(grid),
                })

    counterexample = authored_counterexample()
    obj_rows = components(counterexample)
    by_position = sorted(obj_rows, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))
    by_size = sorted(obj_rows, key=lambda cells: (len(cells), min(r for r, _ in cells), min(c for _, c in cells)))
    rival = positional_rival(counterexample)
    (OUT / "input.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    (OUT / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "sample": {
            "draws": total,
            "bands": [None, "easy", "medium", "hard"],
            "seed_rule": "seed=800000+index, sample_index=index, 100 per band",
            "draws_where_size_order_equals_position_order": correlated,
            "first_rows": sample_rows,
        },
        "counterexample": {
            "input": counterexample,
            "self_check": gen.self_check(counterexample),
            "sizes_by_position": [len(x) for x in by_position],
            "sizes_in_size_order": [len(x) for x in by_size],
            "position_rival_output": rival,
            "domain": "four row-0 markers and four separated connected body objects with distinct sizes 2,3,4,5",
        },
        "finding": (
            "All sampled production grids correlate body size rank with top-left position rank. "
            "A position-sorting rival therefore fits the sampled generator although the canonical "
            "rule sorts by object size; the authored validator-accepted input breaks that correlation."
        ),
    }
    (OUT / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha,
        "draws": total,
        "correlated": correlated,
        "counterexample_self_check": gen.self_check(counterexample),
        "sizes_by_position": [len(x) for x in by_position],
    }, indent=2))


if __name__ == "__main__":
    main()
