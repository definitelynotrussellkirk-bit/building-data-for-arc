#!/usr/bin/env python3
"""Reproduce the invalid CANONICAL_SHORTCUTS declarations for e9905db3a38d."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
SOURCE = WORK / "repo" / "generators" / "e9905db3a38d" / "generator.py"
sys.path.insert(0, str(WORK / "repo" / "shared" / "runtime"))

spec = importlib.util.spec_from_file_location("audit_e9905db3a38d", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

grid = json.loads((HERE / "input.json").read_text())
racket_record = json.loads((HERE / "racket.json").read_text())
racket_output = racket_record["results"][0]["output"]
shortcut_outputs = {
    name: shortcut(grid) for name, shortcut in module.CANONICAL_SHORTCUTS.items()
}
record = {
    "schema": "arcpuzzles-audit-repro-v1",
    "task_id": module.TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "declared_rule_hash": module.RULE_HASH,
    "executed_rule_hash": racket_record["executed_rule_hash"],
    "input_path": str(HERE.relative_to(WORK) / "input.json"),
    "racket_path": str(HERE.relative_to(WORK) / "racket.json"),
    "input_passes_self_check": module.self_check(grid) == [],
    "self_check_errors": module.self_check(grid),
    "canonical_output_equals_python_mirror": module.rule_mirror(grid) == racket_output,
    "shortcut_matches_racket": {
        name: output == racket_output for name, output in shortcut_outputs.items()
    },
    "shortcut_outputs": shortcut_outputs,
    "racket_output": racket_output,
    "finding": (
        "Every declared CANONICAL_SHORTCUT fails this labeled canonical pair; "
        "these competitors belong only in LESSON_COMPETITORS."
    ),
    "command": "python3 checks/audit/e9905db3a38d/repro.py",
    "cwd": str(WORK),
}
(HERE / "repro.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "input_passes_self_check": record["input_passes_self_check"],
    "canonical_output_equals_python_mirror": record["canonical_output_equals_python_mirror"],
    "shortcut_matches_racket": record["shortcut_matches_racket"],
}, indent=2))
if not record["input_passes_self_check"]:
    raise SystemExit(2)
if not record["canonical_output_equals_python_mirror"]:
    raise SystemExit(3)
if any(record["shortcut_matches_racket"].values()):
    raise SystemExit(4)
