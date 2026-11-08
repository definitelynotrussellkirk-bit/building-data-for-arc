#!/usr/bin/env python3
"""Read-only exact-control audit for 70a3e6be3283."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
WORK = OUT.parents[2]
REPO = WORK / "repo"
SOURCE = REPO / "generators/70a3e6be3283/generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))

spec = importlib.util.spec_from_file_location("audit_70a3e6be3283", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

seed = 0
sample_index = 0
difficulty = "easy"
baseline = module.generate(seed, sample_index, difficulty=difficulty)
requested = {"grid_h": 20, "grid_w": 22, "axis": "row", "color": 9}
controlled = module.generate(seed, sample_index, difficulty=difficulty, **requested)
invalid_axis = module.generate(seed, sample_index, difficulty=difficulty, axis="diagonal")
unknown = module.generate(seed, sample_index, difficulty=difficulty, typo_axis=123)

def endpoints(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]

def observed(grid):
    pts = endpoints(grid)
    axis = "row" if pts[0][0] == pts[1][0] else "col"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "axis": axis,
        "color": pts[0][2],
        "endpoints": pts,
        "self_check": module.self_check(grid, difficulty=difficulty),
    }

obs = observed(controlled)
record = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "generator_version": module.VERSION,
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "overrides": requested,
    "declared_axes": {name: module.AXES[name] for name in requested},
    "observed": obs,
    "ignored_exact_controls": [name for name in ("grid_h", "grid_w", "color") if obs[name] != requested[name]],
    "invalid_axis_probe": {
        "overrides": {"axis": "diagonal"},
        "accepted": True,
        "observed": observed(invalid_axis),
    },
    "unknown_override_probe": {
        "overrides": {"typo_axis": 123},
        "accepted": True,
        "same_as_baseline": unknown == baseline,
        "observed": observed(unknown),
    },
    "input": controlled,
    "domain_membership": "actual ordinary generate() output; validator-clean and rule-lawful",
    "finding": "declared grid_h/grid_w/color exact controls are ignored; invalid axis and unknown keys are silently accepted",
    "supported_apply": {
        "cwd": "packet_root",
        "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", module.TASK_ID, "--input", "../checks/audit/70a3e6be3283/input.json", "--out", "../checks/audit/70a3e6be3283/racket.json"],
    },
}
(OUT / "input.json").write_text(json.dumps(controlled, indent=2) + "\n", encoding="utf-8")
(OUT / "counterexample.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "task_id": module.TASK_ID,
    "generator_sha256": record["generator_sha256"],
    "requested": requested,
    "observed": obs,
    "ignored_exact_controls": record["ignored_exact_controls"],
    "invalid_axis_accepted": True,
    "unknown_override_accepted": True,
}, indent=2))
if not record["ignored_exact_controls"] or obs["self_check"]:
    raise SystemExit(1)
