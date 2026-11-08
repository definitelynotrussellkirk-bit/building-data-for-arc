#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
GEN_PATH = REPO / "generators" / "fd9fa5d1f8a3" / "generator.py"
OUT_DIR = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("audit_fd9fa5d1f8a3", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def grid_hash(grid):
    payload = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def summarize(label, overrides):
    grid = mod.generate(1, 0, difficulty="easy", **overrides)
    return {
        "label": label,
        "call": {"seed": 1, "sample_index": 0, "difficulty": "easy", "overrides": overrides},
        "grid": grid,
        "grid_sha256": grid_hash(grid),
        "height": len(grid),
        "width": len(grid[0]),
        "nonzero_count": sum(value != 0 for row in grid for value in row),
        "self_check": mod.self_check(grid, difficulty="easy"),
    }

rows = [
    summarize("base", {}),
    summarize("declared_axis_low", {"n_singletons": 1}),
    summarize("declared_axis_high", {"n_singletons": 12}),
    summarize("actual_internal_key_low", {"singletons": 2}),
    summarize("actual_internal_key_high", {"singletons": 3}),
]

report = {
    "task_id": "fd9fa5d1f8a3",
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "advertised_axis": "n_singletons",
    "internal_draw_key": "singletons",
    "rows": rows,
    "declared_axis_low_equals_base": rows[1]["grid"] == rows[0]["grid"],
    "declared_axis_high_equals_base": rows[2]["grid"] == rows[0]["grid"],
    "declared_axis_low_equals_high": rows[1]["grid"] == rows[2]["grid"],
    "internal_key_changes_output": rows[3]["grid"] != rows[4]["grid"],
}
(OUT_DIR / "reproduction.json").write_text(json.dumps(report, indent=2) + "\n")
(OUT_DIR / "input.json").write_text(json.dumps(rows[2]["grid"], indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))
for row in rows:
    print(row["label"], row["grid_sha256"], row["nonzero_count"], row["self_check"])
