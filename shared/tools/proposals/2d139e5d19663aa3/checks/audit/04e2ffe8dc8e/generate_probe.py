#!/usr/bin/env python3
"""Materialize the exact 04e2ffe8dc8e audit inputs (no target edits)."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "04e2ffe8dc8e"
ROOT = Path.cwd().resolve()
OUTDIR = ROOT.parent / "checks" / "audit" / TASK_ID

module, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)

override_call = {
    "seed": 0,
    "sample_index": 0,
    "difficulty": "medium",
    "texture": "decoy",
    "small_size": 1,
}
override_grid = module.generate(**override_call)
default_calls = [
    {"seed": 0, "sample_index": index, "difficulty": "medium"}
    for index in range(4)
]
default_grids = [module.generate(**call) for call in default_calls]
all_grids = [override_grid, *default_grids]

case = {
    "schema": "arc-audit-inputs-v1",
    "task_id": TASK_ID,
    "generator_source": str(source.relative_to(ROOT)),
    "generator_sha256": source_sha,
    "override_call": override_call,
    "override_self_check": module.self_check(override_grid, difficulty="medium"),
    "override_non_green_nonzero_cells": sum(
        value not in (0, 3) for row in override_grid for value in row
    ),
    "default_calls": default_calls,
    "default_self_checks": [module.self_check(grid, difficulty="medium") for grid in default_grids],
    "inputs_order": ["explicit_decoy_small_size_1", "default_demo_0", "default_demo_1", "default_demo_2", "default_query_3"],
    "inputs": all_grids,
    "target_modified": False,
}
(OUTDIR / "case.json").write_text(json.dumps(case, indent=2) + "\n", encoding="utf-8")
(OUTDIR / "inputs.json").write_text(json.dumps({"inputs": all_grids}, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": source_sha,
    "override_self_check": case["override_self_check"],
    "override_non_green_nonzero_cells": case["override_non_green_nonzero_cells"],
    "default_self_checks": case["default_self_checks"],
    "out": str(OUTDIR / "inputs.json"),
}, indent=2))
