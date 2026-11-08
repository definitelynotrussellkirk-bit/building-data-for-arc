from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import load_selected_generator

TASK = "67702540cb95"
root = Path.cwd()
gen, path, source_sha = load_selected_generator(TASK, root=root)

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def stats(grid):
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "blue_cells": sum(v == 1 for row in grid for v in row),
        "red_cells": sum(v == 2 for row in grid for v in row),
        "self_check": gen.self_check(grid),
        "sha256": digest(grid),
    }

calls = {
    "default": {},
    "grid_h_9": {"grid_h": 9},
    "grid_h_28": {"grid_h": 28},
    "shape_count_1": {"shape_count": 1},
    "shape_count_16": {"shape_count": 16},
    "unknown_axis_7": {"unknown_axis": 7},
}
results = {}
grids = {}
for name, kwargs in calls.items():
    try:
        grid = gen.generate(0, 0, **kwargs)
        grids[name] = grid
        results[name] = {"accepted": True, "kwargs": kwargs, **stats(grid)}
    except Exception as exc:
        results[name] = {
            "accepted": False,
            "kwargs": kwargs,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
base = grids.get("default")
for name, grid in grids.items():
    results[name]["identical_to_default"] = grid == base

report = {
    "schema": "arcpuzzles-audit-contract-probe-v1",
    "task_id": TASK,
    "generator_path": str(path.relative_to(root)),
    "generator_sha256": source_sha,
    "seed": 0,
    "sample_index": 0,
    "finding": (
        "advertised exact axes grid_h and shape_count are ignored, and an unknown "
        "axis is silently accepted; all five override calls return the exact default grid"
    ),
    "results": results,
}
print(json.dumps(report, indent=2, sort_keys=True))
