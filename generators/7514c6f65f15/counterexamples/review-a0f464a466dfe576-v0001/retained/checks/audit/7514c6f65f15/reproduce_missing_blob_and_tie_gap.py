#!/usr/bin/env python3
"""Reproduce 7514c6f65f15's silent two-blob output and tie coverage gap."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve()
PACKET = HERE.parents[4]
REPO = PACKET / "WORK" / "repo"
sys.path[:0] = [str(REPO / "shared" / "runtime"), str(REPO / "src")]
GENERATOR = REPO / "generators" / "7514c6f65f15" / "generator.py"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"

spec = importlib.util.spec_from_file_location("audit_7514c6f65f15", GENERATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def components(grid: list[list[int]]) -> list[dict[str, object]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            result.append(
                {
                    "color": color,
                    "size": len(cells),
                    "bbox_height": max(rows) - min(rows) + 1,
                    "bbox_width": max(cols) - min(cols) + 1,
                    "top_left": [min(rows), min(cols)],
                    "cells": sorted([list(cell) for cell in cells]),
                }
            )
    return result


# Deterministic default sample where the third blob placement exhausts retries.
seed = 0
sample_index = 3
bad_grid = module.generate(seed, sample_index, difficulty=None)
bad_components = components(bad_grid)

# Quantify how often this happens and whether default generation ever teaches ties.
component_count_histogram: Counter[int] = Counter()
tie_count = 0
samples = 0
for difficulty in ("easy", None, "hard"):
    for scan_seed in range(100):
        for scan_index in range(20):
            grid = module.generate(scan_seed, scan_index, difficulty=difficulty)
            comps = components(grid)
            component_count_histogram[len(comps)] += 1
            heights = [int(comp["bbox_height"]) for comp in comps]
            tie_count += int(len(set(heights)) != len(heights))
            samples += 1

canonical_task = None
with CANONICAL.open() as handle:
    for line in handle:
        candidate = json.loads(line)
        if candidate.get("task_id") == module.TASK_ID:
            canonical_task = candidate
            break
assert canonical_task is not None
canonical_train0_components = components(canonical_task["train"][0]["input"])
canonical_train0_heights = [int(comp["bbox_height"]) for comp in canonical_train0_components]

tied_texture = module.generate(0, 0, difficulty="medium", texture="tied_height")

report = {
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "silent_two_blob_counterexample": {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": None,
        "grid": bad_grid,
        "components": bad_components,
        "component_count": len(bad_components),
        "self_check": module.self_check(bad_grid, difficulty=None),
        "contract_claim": "exactly 3 connected blobs",
    },
    "default_scan": {
        "samples": samples,
        "component_count_histogram": dict(sorted(component_count_histogram.items())),
        "height_tie_samples": tie_count,
    },
    "canonical_tie_witness": {
        "train_index": 0,
        "components": canonical_train0_components,
        "bbox_heights": canonical_train0_heights,
        "has_height_tie": len(set(canonical_train0_heights)) != len(canonical_train0_heights),
        "note": "The canonical Racket authority resolves ties by size, then top-left row/column; defaults force unique heights and therefore do not teach that behavior.",
    },
    "declared_tied_height_texture": {
        "components": components(tied_texture),
        "self_check": module.self_check(tied_texture, difficulty="medium"),
    },
    "root_causes": [
        "generate() exits the per-blob retry loop without raising or restarting when a blob cannot obtain a new bbox height.",
        "self_check() requires only at least two colors, not exactly three components with sizes 3/4/5 and distinct heights.",
        "Default generation bans bbox-height ties even though the canonical authority contains and resolves one.",
    ],
}

assert len(bad_components) == 2
assert report["silent_two_blob_counterexample"]["self_check"] == []
assert report["canonical_tie_witness"]["has_height_tie"]
assert tie_count == 0

out = HERE.with_name("reproduction.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
