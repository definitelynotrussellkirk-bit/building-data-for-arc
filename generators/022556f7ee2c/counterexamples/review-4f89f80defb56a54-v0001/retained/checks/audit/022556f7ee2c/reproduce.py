from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parents[4]
WORK = PACKET / "WORK"
sys.path.insert(0, str(WORK / "repo" / "shared" / "runtime"))
SOURCE = WORK / "repo" / "generators" / "022556f7ee2c" / "generator.py"
SPEC = importlib.util.spec_from_file_location("audit_022556f7ee2c", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

SEED = 71
DIFFICULTY = "easy"
INDICES = [0, 1, 2, 3]

def blocker_rival(grid: list[list[int]]) -> list[list[int]]:
    """Incorrect rival: cyan painted earlier becomes an obstacle to later rays."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    emitters = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    for r, c in emitters:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                out[rr][cc] = 8
                rr += dr
                cc += dc
    return out

grids = [GEN.generate(SEED, index, difficulty=DIFFICULTY) for index in INDICES]
payload = {
    "schema": "audit-reproduction-input-v1",
    "task_id": GEN.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": SEED,
    "difficulty": DIFFICULTY,
    "sample_indices": INDICES,
    "self_check": [GEN.self_check(grid, difficulty=DIFFICULTY) for grid in grids],
    "inputs": grids,
    "rival_outputs": [blocker_rival(grid) for grid in grids],
}
Path(__file__).with_name("generated.json").write_text(json.dumps(payload, indent=2) + "\n")
Path(__file__).with_name("inputs.json").write_text(json.dumps(grids, indent=2) + "\n")
print(json.dumps({k: payload[k] for k in ("task_id", "generator_sha256", "seed", "difficulty", "sample_indices", "self_check")}, indent=2))
