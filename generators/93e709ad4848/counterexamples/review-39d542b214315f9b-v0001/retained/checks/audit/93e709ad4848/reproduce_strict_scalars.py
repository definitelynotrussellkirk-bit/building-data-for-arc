#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "93e709ad4848"
REPO = Path.cwd().resolve()
PATH = REPO / "generators" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load audited generator")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

probes = []
for difficulty in ("easy", None, "hard"):
    for value in (True, False, 1.0, 1.75, "1"):
        probes.append(("seed", value, difficulty))
    for value in (True, False, 1.0, 1.75, "1", -1):
        probes.append(("sample_index", value, difficulty))

rows = []
for axis, value, difficulty in probes:
    kwargs = {"seed": 991, "sample_index": 0, "difficulty": difficulty}
    kwargs[axis] = value
    try:
        grid = gen.generate(**kwargs)
    except Exception as exc:
        rows.append({
            "axis": axis,
            "value": value,
            "value_type": type(value).__name__,
            "difficulty": difficulty,
            "accepted": False,
            "error": f"{type(exc).__name__}: {exc}",
        })
    else:
        rows.append({
            "axis": axis,
            "value": value,
            "value_type": type(value).__name__,
            "difficulty": difficulty,
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "grid_sha256": hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest(),
        })

report = {
    "schema": "arcpuzzles-audit-strict-scalar-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(PATH.read_bytes()).hexdigest(),
    "accepted_invalid_count": sum(row["accepted"] for row in rows),
    "total_probes": len(rows),
    "probes": rows,
}
if report["accepted_invalid_count"] != len(rows):
    raise AssertionError(report)
out = Path(__file__).with_name("strict-scalar.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "status": "reproduced",
    "accepted_invalid_count": report["accepted_invalid_count"],
    "total_probes": report["total_probes"],
    "generator_sha256": report["generator_sha256"],
    "output": str(out),
}, sort_keys=True))
