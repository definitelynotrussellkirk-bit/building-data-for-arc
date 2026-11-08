#!/usr/bin/env python3
"""Reproduce exact-control failures for 045c3641f0eb without modifying it."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
SOURCE = WORK / "repo" / "generators" / "045c3641f0eb" / "generator.py"
sys.path.insert(0, str(WORK / "repo" / "shared" / "runtime"))

spec = importlib.util.spec_from_file_location("audit_045c3641f0eb", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

seed = 0
sample_index = 0
grid = module.generate(seed, sample_index, texture="border_touch", n_blobs=3)
h, w = len(grid), len(grid[0])
touches_border = (
    any(grid[0][col] != 0 for col in range(w))
    or any(grid[h - 1][col] != 0 for col in range(w))
    or any(grid[row][0] != 0 for row in range(h))
    or any(grid[row][w - 1] != 0 for row in range(h))
)

try:
    module.generate(15, 0, difficulty="easy", grid_h=10)
except Exception as exc:  # exact exception text is the evidence
    override_error = {"type": type(exc).__name__, "message": str(exc)}
else:
    override_error = None

racket_record = json.loads((HERE / "racket.json").read_text())
record = {
    "schema": "arcpuzzles-audit-repro-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "declared_rule_hash": getattr(module, "RULE_HASH", None),
    "executed_rule_hash": racket_record["executed_rule_hash"],
    "border_touch_case": {
        "seed": seed,
        "sample_index": sample_index,
        "overrides": {"texture": "border_touch", "n_blobs": 3},
        "grid": grid,
        "matches_saved_input": grid == json.loads((HERE / "input.json").read_text()),
        "touches_input_border": touches_border,
        "self_check_errors": module.self_check(grid),
        "racket_output": racket_record["results"][0]["output"],
    },
    "declared_grid_h_axis": module.AXES["grid_h"],
    "easy_grid_h_10_case": {
        "seed": 15,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"grid_h": 10},
        "exception": override_error,
    },
    "finding": (
        "The advertised border_touch texture can produce no border contact, and "
        "a declared-valid grid_h=10 exact override is rejected in the easy band."
    ),
    "command": "python3 checks/audit/045c3641f0eb/repro.py",
    "cwd": str(WORK),
}
(HERE / "repro.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "border_touch_case_touches_border": touches_border,
    "border_touch_case_self_check_errors": module.self_check(grid),
    "easy_grid_h_10_exception": override_error,
}, indent=2))
if touches_border:
    raise SystemExit(2)
if module.self_check(grid):
    raise SystemExit(3)
if not override_error:
    raise SystemExit(4)
