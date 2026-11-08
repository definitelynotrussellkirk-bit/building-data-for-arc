#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
SOURCE = REPO / "generators" / "58bdb4259aa2" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_58bdb4259aa2", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def digest_grid(grid):
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def summarize(grid):
    return {
        "shape": [len(grid), len(grid[0])],
        "nonzero": sum(v != 0 for row in grid for v in row),
        "palette": sorted({v for row in grid for v in row}),
        "grid_sha256": digest_grid(grid),
        "self_check": mod.self_check(grid),
        "grid": grid,
    }

unknown = mod.generate(17, 0, difficulty="medium", typo_axis=1)
dead_false = mod.generate(23, 4, difficulty="medium", anchor_corner=False,
                          asymmetry_force=False, color_count=1)
dead_true = mod.generate(23, 4, difficulty="medium", anchor_corner=True,
                         asymmetry_force=True, color_count=4)
diagonal = mod.generate(31, 2, difficulty="hard", grid_n=11,
                        n_cells=12, position_bias="diagonal")
try:
    mod.generate(0, 0, difficulty="medium", grid_n=7)
except Exception as exc:
    boundary = {"accepted": False, "exception_type": type(exc).__name__, "message": str(exc)}
else:
    boundary = {"accepted": True}

report = {
    "schema": "arcpuzzles-audit-override-counterexample-v1",
    "task_id": mod.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "generator_version": mod.VERSION,
    "cases": {
        "unknown_key_accepted": {"call": {"seed": 17, "sample_index": 0, "difficulty": "medium", "typo_axis": 1}, **summarize(unknown)},
        "dead_controls_false": {"call": {"seed": 23, "sample_index": 4, "difficulty": "medium", "anchor_corner": False, "asymmetry_force": False, "color_count": 1}, **summarize(dead_false)},
        "dead_controls_true": {"call": {"seed": 23, "sample_index": 4, "difficulty": "medium", "anchor_corner": True, "asymmetry_force": True, "color_count": 4}, **summarize(dead_true)},
        "declared_boundary_rejected": {"call": {"seed": 0, "sample_index": 0, "difficulty": "medium", "grid_n": 7}, **boundary},
        "n_cells_not_exact": {"call": {"seed": 31, "sample_index": 2, "difficulty": "hard", "grid_n": 11, "n_cells": 12, "position_bias": "diagonal"}, **summarize(diagonal)},
    },
    "observations": {
        "dead_control_outputs_identical": dead_false == dead_true,
        "requested_n_cells": 12,
        "returned_n_cells": sum(v != 0 for row in diagonal for v in row),
        "unknown_key_validator_clean": mod.self_check(unknown) == [],
    },
    "command": ["python3", "checks/audit/58bdb4259aa2/reproduce_override_contract.py"],
    "working_directory": str(WORK),
}
OUT = HERE.with_name("override-contract-counterexample.json")
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report["observations"], indent=2))
if not (report["observations"]["dead_control_outputs_identical"]
        and report["observations"]["returned_n_cells"] != 12
        and not boundary.get("accepted", True)
        and report["observations"]["unknown_key_validator_clean"]):
    raise SystemExit(1)
