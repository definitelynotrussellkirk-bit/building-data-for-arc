#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "edac81ec2559"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK_ID
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def call(seed=1729, sample_index=3, difficulty=None, **kwargs):
    try:
        grid = GEN.generate(seed, sample_index, difficulty=difficulty, **kwargs)
        return {
            "status": "returned",
            "height": len(grid),
            "width": len(grid[0]),
            "nonzero_cells": sum(value != 0 for row in grid for value in row),
            "distinct_nonzero_colors": len({value for row in grid for value in row if value}),
            "grid": grid,
            "self_check": GEN.self_check(grid, difficulty=difficulty, meta=kwargs),
        }
    except Exception as exc:  # evidence records exact public-call failures
        return {"status": "error", "type": type(exc).__name__, "message": str(exc)}


base = call()
dead_axis_probes = {}
for axis, values in {
    "palette_kind": ["default", "sparse", "dense", "rainbow"],
    "density": ["sparse", "medium", "dense"],
    "n_distinct_colors": [1, 3, 9],
    "texture": ["default", "sparse", "dense", "rainbow"],
}.items():
    cases = []
    for value in values:
        result = call(**{axis: value})
        cases.append({
            "value": value,
            "status": result["status"],
            "same_as_unoverridden": (
                result["status"] == "returned"
                and base["status"] == "returned"
                and grid_key(result["grid"]) == grid_key(base["grid"])
            ),
            "error": None if result["status"] == "returned" else result,
        })
    dead_axis_probes[axis] = cases

advertised_endpoint_probes = {
    "grid_h=4/default": call(grid_h=4),
    "grid_h=14/default": call(grid_h=14),
    "grid_w=4/default": call(grid_w=4),
    "grid_w=16/default": call(grid_w=16),
    "marks=1/default": call(marks=1),
    "marks=20/default": call(marks=20),
}

mark_one_counts = []
for seed in range(40):
    result = call(seed=seed, sample_index=seed, marks=1, difficulty="easy")
    if result["status"] == "returned":
        mark_one_counts.append(result["nonzero_cells"])

strict_scalar_probes = {
    "seed_bool": call(seed=True),
    "seed_float": call(seed=1.5),
    "sample_index_bool": call(sample_index=True),
    "sample_index_negative": call(sample_index=-1),
    "difficulty_unknown": call(difficulty="extreme"),
}

report = {
    "schema": "arcpuzzles-audit-control-contract-v1",
    "task_id": TASK_ID,
    "generator_source": str(SOURCE),
    "generator_sha256": SOURCE_SHA256,
    "declared_rule_hash": getattr(GEN, "RULE_HASH", None),
    "declared_axes": GEN.AXES,
    "base": {key: value for key, value in base.items() if key != "grid"},
    "dead_axis_probes": dead_axis_probes,
    "advertised_endpoint_probes": {
        name: {key: value for key, value in result.items() if key != "grid"}
        for name, result in advertised_endpoint_probes.items()
    },
    "marks_one_cell_counts": {
        "draws": len(mark_one_counts),
        "minimum": min(mark_one_counts) if mark_one_counts else None,
        "maximum": max(mark_one_counts) if mark_one_counts else None,
        "counts": mark_one_counts,
        "note": "The advertised marks axis is consumed as a number of blobs, not an exact number of mark cells.",
    },
    "strict_scalar_probes": {
        name: {key: value for key, value in result.items() if key != "grid"}
        for name, result in strict_scalar_probes.items()
    },
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "control-contract-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA256,
    "declared_rule_hash": report["declared_rule_hash"],
    "dead_axes_all_same": {
        axis: all(case["same_as_unoverridden"] for case in cases)
        for axis, cases in dead_axis_probes.items()
    },
    "marks_one_min_max": [report["marks_one_cell_counts"]["minimum"], report["marks_one_cell_counts"]["maximum"]],
    "endpoint_statuses": {name: result["status"] for name, result in advertised_endpoint_probes.items()},
}, sort_keys=True))
