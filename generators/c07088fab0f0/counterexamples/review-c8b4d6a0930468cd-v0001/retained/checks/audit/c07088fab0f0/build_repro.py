#!/usr/bin/env python3
"""Build the shape-size/orientation schedule shortcut reproducer."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

TASK_ID = "c07088fab0f0"
GENERATOR_PATH = Path("generators") / TASK_ID / "generator.py"
OUT_DIR = Path("../checks/audit") / TASK_ID


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def size_cycle_rival(module, grid):
    """Choose orientation from cell count, not from the missing quadrant."""
    facts = module._analyze(grid)
    if facts["errors"]:
        return [row[:] for row in grid]
    predicted_orientation = (facts["shape_cells"] - 3) % 4
    cells = module._orient(predicted_orientation, facts["canonical_shape"])
    return module._complete_with_shape(grid, cells)


def main() -> None:
    module = load_generator()
    defaults = [module.generate(0, index, difficulty="medium") for index in range(4)]
    counterexample = module.generate(
        0,
        0,
        difficulty="medium",
        shape_cells=3,
        missing_quadrant="bottom_right",
    )
    grids = [*defaults, counterexample]
    rivals = [size_cycle_rival(module, grid) for grid in grids]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
    (OUT_DIR / "rival.json").write_text(json.dumps(rivals, indent=2) + "\n")
    metadata = {
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_rule_hash": module.RULE_HASH,
        "default_lesson": {
            "difficulty": "medium",
            "seed": 0,
            "sample_indices": [0, 1, 2, 3],
            "demo_offsets": [0, 1, 2],
            "query_offset": 3,
            "observed": [module.observe_overrides(grid) for grid in defaults],
        },
        "counterexample": {
            "seed": 0,
            "sample_index": 0,
            "difficulty": "medium",
            "overrides": {"shape_cells": 3, "missing_quadrant": "bottom_right"},
            "observed": module.observe_overrides(counterexample),
            "validator_result": module.self_check(counterexample),
        },
        "rival_description": (
            "Recover a canonical shape from the visible copies, but choose the pasted "
            "orientation as (shape_cells - 3) mod 4 instead of from the missing quadrant. "
            "For seed 0 default indices 0..3, shape size and missing quadrant advance in lockstep."
        ),
    }
    (OUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
