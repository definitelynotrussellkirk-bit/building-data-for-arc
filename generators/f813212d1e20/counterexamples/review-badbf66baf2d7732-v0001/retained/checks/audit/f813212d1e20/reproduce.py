from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK = "f813212d1e20"
repo = Path.cwd()
source = repo / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

small = {"ring_count": 1, "n_decoys": 0, "grid_h": 5, "grid_w": 5}
large = {"ring_count": 7, "n_decoys": 3, "grid_h": 22, "grid_w": 24}
grid_small = mod.generate(0, 0, **small)
grid_large = mod.generate(0, 0, **large)
grid_unknown = mod.generate(0, 0, definitely_unknown_control="ignored")

isolated = [[0] * 5 for _ in range(5)]
isolated[2][2] = 4

def ring_centers(grid):
    border = [(dr, dc) for dr in range(3) for dc in range(3) if (dr, dc) != (1, 1)]
    centers = []
    for r in range(len(grid) - 2):
        for c in range(len(grid[0]) - 2):
            vals = [grid[r + dr][c + dc] for dr, dc in border]
            if grid[r + 1][c + 1] == 0 and vals and 0 not in vals and len(set(vals)) == 1:
                centers.append([r + 1, c + 1])
    return centers

result = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "command": ["python3", "review.py", "run", "python3", "../checks/audit/f813212d1e20/reproduce.py"],
    "payload_cwd": "WORK/repo",
    "cases": {
        "contradictory_exact_overrides": {
            "small_overrides": small,
            "large_overrides": large,
            "outputs_equal": grid_small == grid_large,
            "actual_shape": [len(grid_small), len(grid_small[0])],
            "actual_ring_centers": ring_centers(grid_small),
            "grid": grid_small,
        },
        "unknown_override": {
            "accepted": True,
            "same_as_default": grid_unknown == mod.generate(0, 0),
        },
        "validator_accepts_no_ring": {
            "grid": isolated,
            "ring_centers": ring_centers(isolated),
            "self_check": mod.self_check(isolated),
        },
    },
}
print(json.dumps(result, indent=2))
