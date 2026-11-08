from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "d13d87510a11"
HERE = Path(__file__).resolve().parent
root = find_root(__file__)
gen, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)

grid = gen.generate(
    228,
    0,
    difficulty="easy",
    grid_h=6,
    grid_w=7,
)
counts = {str(color): sum(row.count(color) for row in grid) for color in range(4)}
result = {
    "schema": "audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": source_sha256,
    "source_path": str(source_path.relative_to(root)),
    "recipe": {
        "seed": 228,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"grid_h": 6, "grid_w": 7},
    },
    "dimensions": [len(grid), len(grid[0])],
    "counts_0_to_3": counts,
    "self_check": gen.self_check(grid),
    "input": grid,
}
(HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
(HERE / "probe.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
