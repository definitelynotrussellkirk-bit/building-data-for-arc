#!/usr/bin/env python3
"""Reproduce ee602abaa45a exact-override failure without editing the target."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import hashlib
import json
from pathlib import Path

TARGET = Path("generators/ee602abaa45a/generator.py")
OUT = Path("../checks/audit/ee602abaa45a/ignored-overrides.json")
REQUESTED = {
    "grid_h": 8,
    "grid_w": 12,
    "n_frames": 2,
    "code_a": 3,
    "palette_size": 3,
    "n_distinct_colors": 3,
}

spec = spec_from_file_location("audit_ee602abaa45a", TARGET)
if spec is None or spec.loader is None:
    raise SystemExit(f"cannot load {TARGET}")
module = module_from_spec(spec)
spec.loader.exec_module(module)
grid = module.generate(0, 0, difficulty="medium", **REQUESTED)
record = {
    "schema": "arcpuzzles-audit-override-counterexample-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    "expected_rule_hash_from_lint": "9c5ac46b22bb",
    "call": {
        "seed": 0,
        "sample_index": 0,
        "difficulty": "medium",
        "overrides": REQUESTED,
    },
    "observed": {"grid_h": len(grid), "grid_w": len(grid[0])},
    "counterexample": (len(grid), len(grid[0]))
    != (REQUESTED["grid_h"], REQUESTED["grid_w"]),
    "explanation": (
        "generate() passes overrides into gen_ctx but samples h and w directly "
        "with rng.randint, so exact public overrides are ignored."
    ),
    "command": {
        "cwd": "packet_root",
        "argv": [
            "python3",
            "run_with_racket.py",
            "python3",
            "../checks/audit/ee602abaa45a/reproduce_ignored_overrides.py",
        ],
    },
}
OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps(record, sort_keys=True))
raise SystemExit(0 if record["counterexample"] else 1)
