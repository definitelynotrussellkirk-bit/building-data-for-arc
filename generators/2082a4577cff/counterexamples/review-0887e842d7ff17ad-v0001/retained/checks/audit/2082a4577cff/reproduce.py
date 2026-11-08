"""Reproduce an ordinary lesson window ambiguous about first-vs-all uniform rows."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GEN_PATH = REPO / "generators" / "2082a4577cff" / "generator.py"
EXPECTED_SHA = "e3924c445a074a9173d73638807f37e68858c35246585da5e2c238e134b46303"
assert hashlib.sha256(GEN_PATH.read_bytes()).hexdigest() == EXPECTED_SHA
spec = importlib.util.spec_from_file_location("audit_2082", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def uniform_lines(grid):
    n = len(grid)
    rows = [r for r in range(n) if len(set(grid[r])) == 1]
    cols = [c for c in range(n) if len({grid[r][c] for r in range(n)}) == 1]
    return rows, cols

def render(grid, rows, cols):
    n = len(grid)
    out = [[0] * (n*n) for _ in range(n*n)]
    for r in range(n*n):
        for c in range(n*n):
            if r // n in rows or c // n in cols:
                out[r][c] = grid[r % n][c % n]
    return out

def intended(grid):
    rows, cols = uniform_lines(grid)
    return render(grid, rows[:1], cols[:1])

def every_uniform_line(grid):
    rows, cols = uniform_lines(grid)
    return render(grid, rows, cols)

grids = [mod.generate(20, i, difficulty="easy") for i in range(4)]
assert all(mod.self_check(g, difficulty="easy") == [] for g in grids)
lines = [uniform_lines(g) for g in grids]
assert all(len(rows) <= 1 and len(cols) <= 1 for rows, cols in lines[:3])
assert lines[3] == ([1, 2], [])
record = {
    "task_id": "2082a4577cff",
    "source_sha256": EXPECTED_SHA,
    "generator_call": {"seed": 20, "sample_indices": [0, 1, 2, 3], "difficulty": "easy", "overrides": {}},
    "demo_indices": [0, 1, 2],
    "query_index": 3,
    "uniform_lines": [{"rows": rows, "cols": cols} for rows, cols in lines],
    "inputs": grids,
    "independent_intended_outputs": [intended(g) for g in grids],
    "rival_name": "every_uniform_line",
    "rival_outputs": [every_uniform_line(g) for g in grids],
}
(HERE / "lesson-inputs.json").write_text(json.dumps({"inputs": grids}, indent=2) + "\n")
(HERE / "probe.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"status": "reproduced", "uniform_lines": record["uniform_lines"]}, indent=2))
