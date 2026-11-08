#!/usr/bin/env python3
"""Reproduce the selected override-contract defect without private runner APIs."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "repo/shared/runtime"), str(ROOT / "repo/src")]
TASK = "170ec3daa52f"
SOURCE = ROOT / f"repo/generators/{TASK}/generator.py"
OUT = ROOT / f"checks/audit/{TASK}/override-contract-counterexample.json"

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

overrides = {
    "grid_h": 4,
    "grid_w": 14,
    "variant": 2,
    "palette_kind": "warm",
    "palette_size": 4,
    "position_bias": "three_panels_separated_by_8",
    "n_distinct_colors": 4,
    "density": "dense",
    "texture": "warm",
}
grid = module.generate(0, 0, difficulty="medium", **overrides)
unknown_grid = module.generate(0, 0, difficulty="medium", typo_axis=1)
report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "canonical_rule_hash": "dc39c00f06cc",
    "finding": "advertised exact overrides are ignored and unknown overrides are accepted",
    "seed": 0,
    "sample_index": 0,
    "difficulty": "medium",
    "overrides": overrides,
    "advertised_shape": [4, 14],
    "observed_shape": [len(grid), len(grid[0])],
    "self_check_findings": module.self_check(grid),
    "grid": grid,
    "unknown_override": {
        "kwargs": {"typo_axis": 1},
        "accepted": True,
        "observed_shape": [len(unknown_grid), len(unknown_grid[0])],
        "self_check_findings": module.self_check(unknown_grid),
    },
    "command": ["python3", "checks/audit/170ec3daa52f/reproduce_override_contract.py"],
    "cwd": "packet_root",
}
assert report["observed_shape"] != report["advertised_shape"]
assert report["self_check_findings"] == []
assert report["unknown_override"]["accepted"] is True
assert report["unknown_override"]["self_check_findings"] == []
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "REPRODUCED", "observed_shape": report["observed_shape"]}))
