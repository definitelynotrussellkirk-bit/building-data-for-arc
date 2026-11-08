from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import find_root, load_selected_generator  # noqa: E402


def draw_border(grid, top, left, bottom, right, color):
    for col in range(left, right + 1):
        grid[top][col] = color
        grid[bottom][col] = color
    for row in range(top, bottom + 1):
        grid[row][left] = color
        grid[row][right] = color


# Reverse the vertical color roles: color 3 is north, color 2 is south.
grid = [[0] * 12 for _ in range(9)]
draw_border(grid, 1, 2, 5, 7, 3)
draw_border(grid, 3, 4, 7, 10, 2)
(Path(__file__).parent / "600284beb8e4/input.json").write_text(
    json.dumps(grid, indent=2) + "\n"
)

root = find_root(ROOT)
gen, source, digest = load_selected_generator("a0c6005765ee", root=root)
inputs = [gen.generate(0, index, difficulty="medium") for index in range(9, 13)]
(Path(__file__).parent / "a0c6005765ee/inputs.json").write_text(
    json.dumps(inputs, indent=2) + "\n"
)
(Path(__file__).parent / "a0c6005765ee/generation.json").write_text(
    json.dumps(
        {
            "task_id": "a0c6005765ee",
            "generator_sha256": digest,
            "source": str(source.relative_to(root)),
            "seed": 0,
            "difficulty": "medium",
            "sample_indices": [9, 10, 11, 12],
            "profiles": [gen.observe_overrides(grid)["scene_profile"] for grid in inputs],
            "self_check": [gen.self_check(grid) for grid in inputs],
        },
        indent=2,
    )
    + "\n"
)
