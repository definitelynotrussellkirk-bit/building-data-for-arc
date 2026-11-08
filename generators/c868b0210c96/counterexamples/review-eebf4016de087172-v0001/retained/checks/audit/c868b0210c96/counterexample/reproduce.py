#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[4]
GENERATOR = PACKET / "repo/generators/c868b0210c96/generator.py"
RACKET = Path(__file__).with_name("racket.json")
OUT = Path(__file__).with_name("evidence.json")

spec = importlib.util.spec_from_file_location("audit_c868b0210c96", GENERATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

requested = {"command": 0}
actual = module.generate(0, 0, **requested)
honored = [row[:] for row in actual]
honored[0][1] = 0
unknown = module.generate(0, 0, __override_contract_unknown_axis__=123)

# Count body panels using the documented blank-column split.
def panel_count(grid):
    h, w = len(grid), len(grid[0])
    blank = lambda c: all(grid[r][c] == 0 for r in range(1, h))
    count = 0
    c = 0
    while c < w:
        while c < w and blank(c):
            c += 1
        if c >= w:
            break
        count += 1
        while c < w and not blank(c):
            c += 1
    return count

receipt = json.loads(RACKET.read_text())
report = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": "c868b0210c96",
    "finding": "advertised exact overrides are silently ignored; unknown override keys are accepted",
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "rule_hash": receipt["executed_rule_hash"],
    "seed": 0,
    "sample_index": 0,
    "difficulty": None,
    "requested_overrides": requested,
    "observed": {
        "selector": actual[0][0],
        "command": actual[0][1],
        "n_panels": panel_count(actual),
    },
    "self_check_actual": module.self_check(actual),
    "self_check_with_requested_command_written": module.self_check(honored),
    "unknown_override_accepted": unknown == module.generate(0, 0),
    "actual_generated_input": actual,
    "same_input_with_requested_command_honored": honored,
    "actual_racket_output": receipt["results"][0]["output"],
    "honored_override_racket_output": receipt["results"][1]["output"],
    "outputs_differ": receipt["results"][0]["output"] != receipt["results"][1]["output"],
    "reproduction": {
        "cwd": "packet_root",
        "argv": [
            "env",
            "PYTHONPATH=repo/shared/runtime",
            "python3",
            "checks/audit/c868b0210c96/counterexample/reproduce.py",
        ],
    },
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "observed": report["observed"],
    "unknown_override_accepted": report["unknown_override_accepted"],
    "outputs_differ": report["outputs_differ"],
    "out": str(OUT),
}, indent=2))
