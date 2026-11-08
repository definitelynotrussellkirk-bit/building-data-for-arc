#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "repo/generators/16491c603ea5/generator.py"

spec = importlib.util.spec_from_file_location("audit_16491c603ea5", GENERATOR)
if spec is None or spec.loader is None:
    raise ImportError(GENERATOR)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

cases = [
    {"grid_h": 7.5},
    {"grid_h": "7"},
    {"grid_w": 24.9},
    {"n_decoys": True},
    {"n_decoys": 2.9},
]
rows = []
for index, overrides in enumerate(cases):
    try:
        grid = gen.generate(1, index, difficulty="medium", **overrides)
    except Exception as exc:
        rows.append(
            {
                "overrides": overrides,
                "accepted": False,
                "exception": f"{type(exc).__name__}: {exc}",
            }
        )
        continue
    rows.append(
        {
            "overrides": overrides,
            "accepted": True,
            "observed_overrides": gen.observe_overrides(grid),
            "validator_findings": gen.self_check(grid),
            "grid": grid,
        }
    )

report = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "kind": "invalid_override_type_coercion",
    "task_id": gen.TASK_ID,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "rule_hash": gen.RULE_HASH,
    "axis_contract": gen.AXES,
    "seed": 1,
    "difficulty": "medium",
    "cases": rows,
    "finding": (
        "All five nonconforming exact-control values are accepted and coerced "
        "through int(...), despite AXES declaring integer types."
    ),
    "cwd": "packet_root/WORK",
    "command": [
        "PYTHONPATH=repo/shared/runtime:repo",
        "python3",
        "checks/audit/16491c603ea5-invalid-overrides/reproduce.py",
    ],
}
print(json.dumps(report, indent=2))
