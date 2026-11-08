from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path.cwd()
SOURCE = REPO / "generators/06789067e67f/generator.py"
spec = importlib.util.spec_from_file_location("audit_06789067e67f", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

seed = 20261011
sample_index = 7
single = module.generate(
    seed,
    sample_index,
    difficulty="medium",
    texture="single_component",
)
single_errors = module.self_check(single, difficulty="medium")

plain = module.generate(
    seed,
    sample_index,
    difficulty="medium",
    texture="plain",
)
bogus = module.generate(
    seed,
    sample_index,
    difficulty="medium",
    texture="not_a_declared_texture",
)

endpoint_results = {}
for axis, value in (("grid_h", 10), ("grid_h", 18), ("grid_w", 12), ("grid_w", 22)):
    key = f"{axis}={value}"
    try:
        grid = module.generate(seed, sample_index, difficulty="medium", **{axis: value})
    except Exception as exc:  # evidence captures the public behavior exactly
        endpoint_results[key] = {
            "accepted": False,
            "exception": type(exc).__name__,
            "message": str(exc),
        }
    else:
        endpoint_results[key] = {
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "self_check": module.self_check(grid, difficulty="medium"),
        }

out = {
    "schema": "audit-probe-v1",
    "task_id": module.TASK_ID,
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "missing_rule_hash": not hasattr(module, "RULE_HASH"),
    "single_component": {
        "shape": [len(single), len(single[0])],
        "self_check": single_errors,
        "nonzero_cells": sum(value != 0 for row in single for value in row),
    },
    "unknown_texture": {
        "accepted": True,
        "equals_plain_same_seed": bogus == plain,
        "self_check": module.self_check(bogus, difficulty="medium"),
    },
    "advertised_endpoint_results": endpoint_results,
}

out_path = REPO / "../checks/audit/06789067e67f/probe.json"
input_path = REPO / "../checks/audit/06789067e67f/single_component_input.json"
out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
input_path.write_text(json.dumps(single, indent=2) + "\n")
print(json.dumps(out, indent=2, sort_keys=True))

assert out["missing_rule_hash"] is True
assert single_errors and "expected 2-4 components, got 1" in single_errors
assert bogus == plain
assert all(not row["accepted"] for row in endpoint_results.values())
