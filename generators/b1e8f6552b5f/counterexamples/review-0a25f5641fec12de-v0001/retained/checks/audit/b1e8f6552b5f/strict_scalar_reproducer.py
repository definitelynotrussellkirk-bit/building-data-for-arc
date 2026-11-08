#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators/b1e8f6552b5f/generator.py"
OUT = Path(__file__).resolve().parent / "strict_scalar_reproducer.json"

spec = importlib.util.spec_from_file_location("audit_b1e8f6552b5f", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

records = []
for value in (True, False, -1):
    row = {"seed": 0, "sample_index": value, "sample_index_type": type(value).__name__}
    try:
        grid = module.generate(0, value, difficulty="medium")
        row.update(
            {
                "status": "accepted_invalid_scalar",
                "shape": [len(grid), len(grid[0])],
                "self_check": module.self_check(grid),
                "grid_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
            }
        )
    except Exception as exc:
        row.update({"status": "rejected", "error": f"{type(exc).__name__}: {exc}"})
    records.append(row)

payload = {
    "schema": "arcpuzzles-audit-strict-scalar-v1",
    "task_id": module.TASK_ID,
    "generator_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": module.RULE_HASH,
    "claim": "sample_index must be a nonnegative literal integer; bool and negative integers are accepted",
    "records": records,
    "all_invalid_values_accepted": all(row["status"] == "accepted_invalid_scalar" for row in records),
}
OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print(json.dumps({"all_invalid_values_accepted": payload["all_invalid_values_accepted"], "source": payload["generator_source_sha256"]}))
