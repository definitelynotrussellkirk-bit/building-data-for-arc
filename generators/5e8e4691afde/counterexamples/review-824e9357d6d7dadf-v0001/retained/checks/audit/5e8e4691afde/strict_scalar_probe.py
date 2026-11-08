#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "5e8e4691afde"
HERE = Path(__file__).resolve().parent
root = find_root(__file__)
generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
invalid_seed = [True, False, 1.0, 1.75, "1"]
invalid_sample = [True, False, 1.0, 1.75, "1", -1]
results = []


def grid_sha256(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


for difficulty in (None, "easy", "hard"):
    for axis, values in (("seed", invalid_seed), ("sample_index", invalid_sample)):
        for value in values:
            kwargs = {"seed": 0, "sample_index": 0, "difficulty": difficulty}
            kwargs[axis] = value
            try:
                grid = generator.generate(**kwargs)
            except Exception as exc:
                results.append({
                    "axis": axis,
                    "value": value,
                    "value_type": type(value).__name__,
                    "difficulty": difficulty,
                    "status": "rejected",
                    "exception": f"{type(exc).__name__}: {exc}",
                })
            else:
                results.append({
                    "axis": axis,
                    "value": value,
                    "value_type": type(value).__name__,
                    "difficulty": difficulty,
                    "status": "accepted_invalid_scalar",
                    "grid_sha256": grid_sha256(grid),
                    "self_check": generator.self_check(grid),
                })

accepted = [row for row in results if row["status"] == "accepted_invalid_scalar"]
report = {
    "schema": "arcpuzzles-audit-strict-scalar-v1",
    "task_id": TASK_ID,
    "generator_path": str(source_path.relative_to(root)),
    "generator_sha256": source_sha256,
    "generator_version": generator.VERSION,
    "finding": "generate accepts booleans, non-integral floats, strings, and negative sample indices as runtime scalars",
    "difficulties": [None, "easy", "hard"],
    "probe_count": len(results),
    "accepted_invalid_count": len(accepted),
    "rejected_count": len(results) - len(accepted),
    "results": results,
    "scope": "direct public generate calls; output labels were not evaluated because the contract defect occurs before rule execution",
}
(HERE / "strict-scalar-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"probe_count": len(results), "accepted_invalid_count": len(accepted), "source_sha256": source_sha256}, sort_keys=True))
assert len(results) == 33
assert len(accepted) == 33
