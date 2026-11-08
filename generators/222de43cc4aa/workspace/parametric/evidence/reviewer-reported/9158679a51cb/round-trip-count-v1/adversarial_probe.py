#!/usr/bin/env python3
"""Bounded adversarial pass for the retained round-trip-count evidence."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3] / "repo"
PROTOTYPE = REPO / "generators/222de43cc4aa/workspace/parametric/prototype.py"
spec = importlib.util.spec_from_file_location("round_trip_adversarial_prototype", PROTOTYPE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

from arc_repl.racket_bridge import RacketBridge

root = Path(__file__).resolve().parent
boundary_inputs = [
    [[1], [2], [3]],
    [[(row + col) % 10 for col in range(30)] for row in range(8)],
]
checks = []
with RacketBridge(max_calls_before_restart=64) as bridge:
    for setting in module.ALLOWED_ROUND_TRIPS:
        actual = module.execute_rule_many(module.rule_source(setting), boundary_inputs, bridge=bridge)
        expected = [module.python_mirror(grid, setting) for grid in boundary_inputs]
        assert actual == expected
        checks.append({
            "round_trips": setting,
            "input_shapes": [[len(grid), len(grid[0])] for grid in boundary_inputs],
            "output_shapes": [[len(grid), len(grid[0])] for grid in actual],
            "racket_python_parity": True,
        })
    runtime_identity = bridge.runtime_identity

invalid_results = []
for name, callable_ in [
    ("bool_setting", lambda: module.rule_source(True)),
    ("too_large_setting", lambda: module.rule_source(3)),
    ("bool_cell", lambda: module.python_mirror([[True], [1]], 1)),
    ("ragged_grid", lambda: module.python_mirror([[1], [2, 3]], 1)),
    ("too_tall_grid", lambda: module.python_mirror([[0] for _ in range(9)], 2)),
]:
    try:
        callable_()
    except ValueError as exc:
        invalid_results.append({"case": name, "rejected": True, "message": str(exc)})
    else:
        raise AssertionError(f"invalid case accepted: {name}")

privacy = []
for public_path in sorted((root / "public").glob("*.json")):
    payload = public_path.read_bytes()
    visible = json.loads(payload)
    assert hashlib.sha256(payload).hexdigest() == public_path.stem
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])
    privacy.append({
        "public_id": public_path.stem,
        "visible_byte_hash_matches_filename": True,
        "query_answers_absent": True,
    })

structural = module.verify_evidence(root)
result = {
    "schema": "222de43cc4aa-round-trip-adversarial-v1",
    "status": "pass",
    "surfaces": ["parameter/Racket parity", "public/private export and numeric types"],
    "racket_application_count": len(boundary_inputs) * len(module.ALLOWED_ROUND_TRIPS),
    "boundary_checks": checks,
    "invalid_rejections": invalid_results,
    "public_privacy": privacy,
    "structural_verification": structural,
    "runtime_identity": runtime_identity,
    "remaining_limit": "Bounded to two shape boundaries and declared finite settings; no arbitrary-program uniqueness claim.",
}
(root / "private/adversarial-check.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(json.dumps(result, indent=2, sort_keys=True))
