from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "d30c6cb51dac"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def normalized_shape(panel):
    cells = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0]
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def panel_shapes(grid):
    n = (len(grid[0]) + 1) // 6
    shapes = []
    for index in range(n):
        start = 6 * index
        panel = [row[start:start + 5] for row in grid]
        shapes.append(normalized_shape(panel))
    return shapes


def bbox(shape):
    return (1 + max(r for r, _ in shape), 1 + max(c for _, c in shape))


def bbox_nonidentity_rival(grid):
    shapes = panel_shapes(grid)
    return [
        [
            8 if i == j else 2 if bbox(a) == bbox(b) and a != b else 0
            for j, b in enumerate(shapes)
        ]
        for i, a in enumerate(shapes)
    ]


def pair(sample_index):
    grid = gen.generate(0, sample_index, difficulty="easy")
    return {"input": grid, "output": gen.rule_mirror(grid)}


demos = [pair(1), pair(2)]
query_grid = gen.generate(0, 3, difficulty="easy")
query_truth = gen.rule_mirror(query_grid)
query_rival = bbox_nonidentity_rival(query_grid)
findings = gen.lesson_identifiable(demos, {"input": query_grid})
rival_fits = [bbox_nonidentity_rival(item["input"]) == item["output"] for item in demos]
self_check = gen.self_check(query_grid)

assert all(rival_fits)
assert query_rival != query_truth
assert findings == []
assert self_check == []

query_bytes = json.dumps(query_grid, separators=(",", ":")).encode()
report = {
    "schema": "d30_bbox_shortcut_probe/1",
    "task_id": TASK_ID,
    "generator_path": str(source_path.relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "seed": 0,
    "difficulty": "easy",
    "demo_sample_indices": [1, 2],
    "query_sample_index": 3,
    "profiles": [gen.schedule_profile(0, i, "easy") for i in (1, 2, 3)],
    "query_input_sha256": hashlib.sha256(query_bytes).hexdigest(),
    "query_panel_bbox_dimensions": [list(bbox(shape)) for shape in panel_shapes(query_grid)],
    "rival": "same cropped bounding-box dimensions and nonidentity",
    "rival_fits_demo": rival_fits,
    "lesson_identifiable_findings": findings,
    "query_self_check": self_check,
    "truth_matrix_python_mirror": query_truth,
    "rival_matrix": query_rival,
    "differing_cells": [
        [r, c]
        for r in range(len(query_truth))
        for c in range(len(query_truth))
        if query_truth[r][c] != query_rival[r][c]
    ],
}
(HERE / "query-input.json").write_text(json.dumps(query_grid, indent=2) + "\n")
(HERE / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
