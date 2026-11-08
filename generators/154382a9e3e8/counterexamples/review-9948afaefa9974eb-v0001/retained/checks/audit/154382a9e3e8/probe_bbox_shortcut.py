"""Audit probe: bounding-box area shortcut for 154382a9e3e8."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "154382a9e3e8"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(cells)
    return out


def bbox_area(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def bbox_rival(grid):
    out = [row[:] for row in grid]
    mapping = {4: 1, 3: 2, 2: 3}
    for cells in components(grid):
        color = mapping.get(bbox_area(cells), 5)
        for r, c in cells:
            out[r][c] = color
    return out


sampled = 0
sampled_components = 0
nonrect_target = []
for band in ("easy", "medium", "hard"):
    for index in range(100):
        grid = GEN.generate(881731, index, difficulty=band)
        if GEN.self_check(grid):
            continue
        sampled += 1
        for cells in components(grid):
            size = len(cells)
            if size in (2, 3, 4):
                sampled_components += 1
                if bbox_area(cells) != size:
                    nonrect_target.append(
                        {"band": band, "index": index, "size": size, "bbox_area": bbox_area(cells)}
                    )

pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
witness = None
for pair_index, pair in enumerate(pairs):
    rival = bbox_rival(pair["input"])
    if rival != pair["output"]:
        mismatches = []
        for cells in components(pair["input"]):
            size = len(cells)
            area = bbox_area(cells)
            if size != area:
                mismatches.append({"size": size, "bbox_area": area, "cells": cells})
        witness = {
            "pair_index": pair_index,
            "input": pair["input"],
            "canonical_output": pair["output"],
            "bbox_area_rival_output": rival,
            "nonrectangular_components": mismatches,
        }
        break

report = {
    "task_id": TASK_ID,
    "generator_source": str(Path(SOURCE).relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA,
    "sample_seed": 881731,
    "sampled_valid_grids": sampled,
    "sampled_size_2_3_4_components": sampled_components,
    "sampled_nonrectangular_target_components": nonrect_target,
    "shortcut_fits_sampled_domain": not nonrect_target,
    "canonical_counterexample": witness,
}
print(json.dumps(report, indent=2, sort_keys=True))
