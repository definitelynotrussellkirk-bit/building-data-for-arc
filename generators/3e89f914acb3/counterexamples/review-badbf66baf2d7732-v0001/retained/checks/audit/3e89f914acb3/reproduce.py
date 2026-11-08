from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK = "3e89f914acb3"
repo = Path.cwd()
source = repo / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

overrides = {
    "grid_h": 10,
    "grid_w": 10,
    "seeds": 5,
    "n_distinct_colors": 1,
    "palette_size": 1,
    "palette_kind": "warm",
    "texture": "warm",
}
grid = mod.generate(0, 0, **overrides)
nonzero = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]

adjacent = [[0] * 6 for _ in range(6)]
adjacent[2][2] = 4
adjacent[2][3] = 7

result = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "command": ["python3", "review.py", "run", "python3", "../checks/audit/3e89f914acb3/reproduce.py"],
    "payload_cwd": "WORK/repo",
    "cases": {
        "one_color_request": {
            "overrides": overrides,
            "actual_shape": [len(grid), len(grid[0])],
            "requested_seed_count": 5,
            "actual_seed_count": len(nonzero),
            "requested_distinct_colors": 1,
            "actual_distinct_colors": sorted({value for _, _, value in nonzero}),
            "self_check": mod.self_check(grid),
            "grid": grid,
        },
        "validator_accepts_adjacent_seeds": {
            "grid": adjacent,
            "manhattan_distance": 1,
            "self_check": mod.self_check(adjacent),
        },
    },
}
print(json.dumps(result, indent=2))
