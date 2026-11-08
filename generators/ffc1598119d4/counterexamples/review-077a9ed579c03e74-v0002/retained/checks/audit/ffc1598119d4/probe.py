from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
SOURCE = REPO / "generators" / "ffc1598119d4" / "generator.py"
SPEC = importlib.util.spec_from_file_location("audited_ffc1598119d4", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

seed = 0
sample_index = 0
difficulty = "medium"
cases = {
    "default": {},
    "code_a_1": {"code_a": 1},
    "code_a_4": {"code_a": 4},
    "source_colors_1": {"source_colors": 1},
    "source_colors_7": {"source_colors": 7},
    "grid_h_8": {"grid_h": 8},
    "grid_h_30": {"grid_h": 30},
}
grids = {
    name: GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)
    for name, overrides in cases.items()
}
report = {
    "schema": "audit-override-counterexample-v1",
    "task_id": GEN.TASK_ID,
    "version": GEN.VERSION,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "cases": {
        name: {
            "overrides": cases[name],
            "grid_sha256": digest(grid),
            "shape": [len(grid), len(grid[0])],
        }
        for name, grid in grids.items()
    },
    "equalities": {
        "code_a_1_equals_code_a_4": grids["code_a_1"] == grids["code_a_4"],
        "source_colors_1_equals_source_colors_7": grids["source_colors_1"] == grids["source_colors_7"],
        "grid_h_8_equals_grid_h_30": grids["grid_h_8"] == grids["grid_h_30"],
        "all_equal_default": all(grid == grids["default"] for grid in grids.values()),
    },
    "command": [
        "python3",
        "../checks/audit/ffc1598119d4/probe.py",
    ],
    "cwd": "repo",
}
Path(__file__).with_name("counterexample.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
