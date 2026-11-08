#!/usr/bin/env python3
"""Build the default-lesson profile-shortcut reproducer for ec9cf2c80d58."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

TASK_ID = "ec9cf2c80d58"
GENERATOR_PATH = Path("generators") / TASK_ID / "generator.py"
OUT_DIR = Path("../checks/audit") / TASK_ID


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def profile_template_rival(module, grid):
    """Use a special teaching template; otherwise erase perpendicular to bands."""
    layout = module._layout(grid)
    if layout is None:
        return [row[:] for row in grid]
    orientation, bands = layout
    height, width = len(grid), len(grid[0])
    holes = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0]
    teaching = (
        orientation == "vertical"
        and len(bands) == 2
        and width == 2 * (height - 1)
        and len(holes) == 3
    )
    result = [row[:] for row in grid]
    for row, col in holes:
        color = module._neighbor(grid, row, col)
        if color is None:
            continue
        if teaching:
            clear_column = sum(other_row == row for other_row, _ in holes) >= 2
        else:
            clear_column = orientation == "horizontal"
        cells = (
            ((r, col) for r in range(height))
            if clear_column
            else ((row, c) for c in range(width))
        )
        for r, c in cells:
            if grid[r][c] in (0, color):
                result[r][c] = 0
    return result


def main() -> None:
    module = load_generator()
    difficulty = "easy"
    seed = 2
    sample_indices = [7, 8, 9, 10]
    grids = [module.generate(seed, index, difficulty=difficulty) for index in sample_indices]
    rivals = [profile_template_rival(module, grid) for grid in grids]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
    (OUT_DIR / "rival.json").write_text(json.dumps(rivals, indent=2) + "\n")
    metadata = {
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_rule_hash": module.RULE_HASH,
        "difficulty": difficulty,
        "seed": seed,
        "sample_indices": sample_indices,
        "query_offset": 3,
        "profiles": [module.schedule_profile(seed, index, difficulty) for index in sample_indices],
        "observed": [module.observe_overrides(grid) for grid in grids],
        "validator_results": [module.self_check(grid) for grid in grids],
        "rival_description": (
            "Recognize the fixed teaching profile and clear columns for holes sharing a row, "
            "rows for other teaching holes; on every other profile, erase perpendicular to "
            "the visible band orientation. This never compares row/column extents."
        ),
    }
    (OUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
