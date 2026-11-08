#!/usr/bin/env python3
"""Reproduce ea45d5e1d11c canonical-validator rejection without editing target."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = "ea45d5e1d11c"
SOURCE_PATH = ROOT / "repo" / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK}_generator", SOURCE_PATH)
assert spec is not None and spec.loader is not None
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)
input_path = ROOT / "checks" / "audit" / TASK / "input.json"
racket_path = ROOT / "checks" / "audit" / TASK / "racket.json"
grid = json.loads(input_path.read_text())
racket = json.loads(racket_path.read_text())
source_path = SOURCE_PATH
source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
errors_by_difficulty = {
    str(difficulty): GEN.self_check(grid, difficulty=difficulty)
    for difficulty in (None, "easy", "medium", "hard")
}
result = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": TASK,
    "finding_kind": "reproduced canonical-validator rejection",
    "documented_domain": True,
    "domain_reason": "Exact canonical training input, row source=training, train pair index 0.",
    "generator_sha256": source_hash,
    "rule_hash": racket["executed_rule_hash"],
    "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
    "input": grid,
    "actual_racket_output": racket["results"][0]["output"],
    "rival_output": None,
    "validator": {
        "self_check_errors_by_difficulty": errors_by_difficulty,
        "canonical_default_is_rejected": bool(errors_by_difficulty["None"]),
    },
    "reproducer": {
        "cwd": racket["cwd"],
        "apply_command": racket["command"],
        "probe_command": [
            "python3", "run_with_racket.py", "python3",
            "../checks/audit/ea45d5e1d11c/probe.py",
        ],
    },
    "battery_summary": "checks/audit/ea45d5e1d11c/battery/checks/ea45d5e1d11c_after_battery_summary.json",
}
out = ROOT / "checks" / "audit" / TASK / "counterexample.json"
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({
    "generator_sha256": source_hash,
    "rule_hash": result["rule_hash"],
    "default_self_check_errors": errors_by_difficulty["None"],
    "hard_self_check_errors": errors_by_difficulty["hard"],
    "counterexample": str(out.relative_to(ROOT)),
}, indent=2))
