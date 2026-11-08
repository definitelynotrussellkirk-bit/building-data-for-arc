#!/usr/bin/env python3
"""Reproduce the validator/domain mismatch for audit target 16296fabf4b4."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK_ID = "16296fabf4b4"
GEN_PATH = ROOT / "repo" / "generators" / TASK_ID / "generator.py"
INPUT_PATH = Path(__file__).with_name("input.json")
RACKET_PATH = Path(__file__).with_name("racket.json")
OUT_PATH = Path(__file__).with_name("counterexample.json")

sys.path.insert(0, str(ROOT / "repo" / "shared" / "runtime"))
spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {GEN_PATH}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

grid = json.loads(INPUT_PATH.read_text())
racket = json.loads(RACKET_PATH.read_text())
actual = racket["results"][0]["output"]
validator_errors = module.self_check(grid, difficulty="easy", meta=None)
record = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": TASK_ID,
    "finding": (
        "validator admits a wide-only identity scene despite the documented "
        "invariant requiring at least one tall and one non-tall component"
    ),
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash": racket["executed_rule_hash"],
    "seed": None,
    "sample_index": None,
    "overrides": None,
    "input": grid,
    "validator_call": {"difficulty": "easy", "meta": None},
    "validator_errors": validator_errors,
    "passes_target_validator": validator_errors == [],
    "belongs_to_documented_nondegenerate_domain": False,
    "domain_reason": (
        "contains one wide component and no tall component; INVARIANTS require "
        "at least one of each"
    ),
    "actual_racket_output": actual,
    "rival_name": "identity",
    "rival_output": grid,
    "rival_matches_actual": grid == actual,
    "supported_apply_evidence": f"checks/audit/{TASK_ID}/racket.json",
    "supported_apply_command": racket["command"],
    "supported_apply_cwd": "repo",
}
OUT_PATH.write_text(json.dumps(record, indent=2) + "\n")
if not (record["passes_target_validator"] and record["rival_matches_actual"]):
    raise SystemExit(1)
print(json.dumps({
    "generator_sha256": record["generator_sha256"],
    "rule_hash": record["rule_hash"],
    "validator_errors": record["validator_errors"],
    "rival_matches_actual": record["rival_matches_actual"],
}, indent=2))
