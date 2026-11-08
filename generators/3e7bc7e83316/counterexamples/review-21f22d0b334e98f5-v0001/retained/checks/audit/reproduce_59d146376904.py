#!/usr/bin/env python3
"""Small public-API reproducer for audit target 59d146376904."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACKET_ROOT = Path(__file__).resolve().parents[2]
SOURCE = PACKET_ROOT / "repo/generators/59d146376904/generator.py"
OUT = PACKET_ROOT / "checks/audit/59d146376904-reproducer.json"

spec = importlib.util.spec_from_file_location("audit_target_59d146376904", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import {SOURCE}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

override_request = {
    "seed": 0,
    "sample_index": 0,
    "difficulty": "easy",
    "overrides": {"grid_h": 4},
}
grid = module.generate(
    override_request["seed"],
    override_request["sample_index"],
    difficulty=override_request["difficulty"],
    **override_request["overrides"],
)
tied = module._draw_from_degenerate("tied_majority", None)

payload = {
    "schema": "arcpuzzles-audit-reproducer-v1",
    "task_id": "59d146376904",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "declared_version": module.VERSION,
    "rule_hash": None,
    "command": [
        "env",
        "PYTHONPATH=repo/shared/runtime:repo",
        "python3",
        "checks/audit/reproduce_59d146376904.py",
    ],
    "cwd": "packet_root",
    "override_contract_failure": {
        "request": override_request,
        "expected_dimensions": [4, 6],
        "observed_dimensions": [len(grid), len(grid[0])],
        "self_check_errors": module.self_check(grid, difficulty="easy"),
        "input_grid": grid,
    },
    "validator_false_acceptance": {
        "fixture": "tied_majority",
        "documented_reason_invalid": "top-left quadrant has a 2-to-2 tie, so no strict majority exists",
        "self_check_errors": module.self_check(tied),
        "input_grid": tied,
    },
}
OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(OUT.relative_to(PACKET_ROOT))
print(json.dumps({
    "generator_sha256": payload["generator_sha256"],
    "override_observed": payload["override_contract_failure"]["observed_dimensions"],
    "tied_majority_self_check": payload["validator_false_acceptance"]["self_check_errors"],
}, sort_keys=True))
