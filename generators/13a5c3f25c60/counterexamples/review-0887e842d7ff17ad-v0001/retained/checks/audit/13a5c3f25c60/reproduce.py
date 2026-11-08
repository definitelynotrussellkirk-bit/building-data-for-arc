"""Reproduce an ordinary lesson window ambiguous about row-0 body cells."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GEN_PATH = REPO / "generators" / "13a5c3f25c60" / "generator.py"
EXPECTED_SHA = "3466b8d49cea0c02ec043d8793d00585d07dd28db3edeac85af3a807207fec48"
assert hashlib.sha256(GEN_PATH.read_bytes()).hexdigest() == EXPECTED_SHA
spec = importlib.util.spec_from_file_location("audit_13a5", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def intended(grid):
    src, tgt = grid[0][0], grid[0][-1]
    return [[
        tgt if value == src and not (r == 0 and c in (0, len(row)-1)) else value
        for c, value in enumerate(row)
    ] for r, row in enumerate(grid)]

def below_top_row_only(grid):
    """Plausible shortcut: corner legend applies only below the legend row."""
    src, tgt = grid[0][0], grid[0][-1]
    return [[tgt if r > 0 and value == src else value for value in row]
            for r, row in enumerate(grid)]

grids = [mod.generate(13, i, difficulty="easy") for i in range(4)]
assert all(mod.self_check(g, difficulty="easy") == [] for g in grids)
row0_hits = [[c for c in range(1, len(g[0])-1) if g[0][c] == g[0][0]] for g in grids]
assert row0_hits[:3] == [[], [], []]
assert row0_hits[3] == [3, 6]
record = {
    "task_id": "13a5c3f25c60",
    "source_sha256": EXPECTED_SHA,
    "generator_call": {"seed": 13, "sample_indices": [0, 1, 2, 3], "difficulty": "easy", "overrides": {}},
    "demo_indices": [0, 1, 2],
    "query_index": 3,
    "row0_source_columns": row0_hits,
    "inputs": grids,
    "independent_intended_outputs": [intended(g) for g in grids],
    "rival_name": "below_top_row_only",
    "rival_outputs": [below_top_row_only(g) for g in grids],
}
(HERE / "lesson-inputs.json").write_text(json.dumps({"inputs": grids}, indent=2) + "\n")
(HERE / "probe.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"status": "reproduced", "row0_source_columns": row0_hits}, indent=2))
