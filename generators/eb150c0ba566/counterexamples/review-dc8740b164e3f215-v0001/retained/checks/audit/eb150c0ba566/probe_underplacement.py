from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK = "eb150c0ba566"
root = Path.cwd()
gen, source_path, source_sha = load_selected_generator(TASK, root=root)
overrides = {"grid_h": 9, "grid_w": 7, "n_seeds": 3}
grid = gen.generate(0, 0, difficulty="easy", **overrides)
seeds = [(r, c, grid[r][c]) for r in range(4, len(grid)) for c in range(len(grid[0])) if grid[r][c] in {2, 3}]
result = {
    "schema": "audit-counterexample-v1",
    "task_id": TASK,
    "generator_source": str(source_path.relative_to(root)),
    "generator_sha256": source_sha,
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "overrides": overrides,
    "observed": {"grid_h": len(grid), "grid_w": len(grid[0]), "n_seeds": len(seeds)},
    "seed_cells": seeds,
    "self_check": gen.self_check(grid, difficulty="easy"),
    "input": grid,
    "finding": "n_seeds=3 is silently under-placed as 2 on the minimum easy board while self_check accepts it",
}
out = Path(__file__).with_name("underplacement.json")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
