#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PACKET_ROOT / "repo/shared/runtime"))
GENERATOR_PATH = PACKET_ROOT / "repo/generators/d50ba3ef0962/generator.py"
OUT = Path(__file__).with_name("dead-controls.json")

spec = importlib.util.spec_from_file_location("audit_d50_generator", GENERATOR_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


seed = 123
sample_index = 5
cases = {
    "palette_kind=warm": {"palette_kind": "warm"},
    "palette_kind=cool": {"palette_kind": "cool"},
    "grid_w=9": {"grid_w": 9},
    "grid_w=18": {"grid_w": 18},
}
records = {}
for name, overrides in cases.items():
    grid = module.generate(seed, sample_index, **overrides)
    records[name] = {
        "overrides": overrides,
        "height": len(grid),
        "width": len(grid[0]),
        "grid_sha256": grid_hash(grid),
        "self_check": module.self_check(grid),
        "grid": grid,
    }

report = {
    "schema": "arcpuzzles-audit-dead-controls-v1",
    "task_id": "d50ba3ef0962",
    "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
    "seed": seed,
    "sample_index": sample_index,
    "cases": records,
    "palette_outputs_equal": records["palette_kind=warm"]["grid"] == records["palette_kind=cool"]["grid"],
    "grid_w_outputs_equal": records["grid_w=9"]["grid"] == records["grid_w=18"]["grid"],
    "all_four_outputs_equal": len({record["grid_sha256"] for record in records.values()}) == 1,
    "all_self_checks_pass": all(record["self_check"] == [] for record in records.values()),
    "finding": (
        "Declared exact controls palette_kind and grid_w are accepted but do not alter output; "
        "valid user intent is silently ignored."
    ),
    "command": ["python3", "checks/audit/d50ba3ef0962/reproduce_dead_controls.py"],
    "cwd": "packet_root",
}
OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: report[k] for k in (
    "task_id", "generator_sha256", "palette_outputs_equal", "grid_w_outputs_equal",
    "all_four_outputs_equal", "all_self_checks_pass")}, indent=2))
