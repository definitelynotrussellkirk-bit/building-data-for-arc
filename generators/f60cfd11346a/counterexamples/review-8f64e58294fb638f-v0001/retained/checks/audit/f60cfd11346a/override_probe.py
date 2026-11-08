#!/usr/bin/env python3
"""Measure whether advertised exact dimension overrides are consumed."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
TASK = "f60cfd11346a"
SOURCE = REPO / "generators" / TASK / "generator.py"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from puzzle_generators import base

spec = importlib.util.spec_from_file_location("audit_override_generator", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load generator")
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)

rows = []
contexts = []
base.set_ctx_observer(contexts.append)
try:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(10):
            seed = 710_000 + band_index * 100 + offset
            sample_index = 900 + offset
            requested = {"grid_h": 18, "grid_w": 24}
            grid = GEN.generate(seed, sample_index, difficulty=band, **requested)
            ctx = contexts[-1]
            rows.append(
                {
                    "difficulty": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "requested": requested,
                    "observed": {"grid_h": len(grid), "grid_w": len(grid[0])},
                    "recorded_draws": ctx.recorded_draws(),
                    "overrides_used": ctx.overrides_used(),
                    "self_check_errors": GEN.self_check(grid, difficulty=band),
                }
            )
finally:
    base.set_ctx_observer(None)

report = {
    "schema": "arc-audit-override-consumption-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "generator_version": GEN.VERSION,
    "requested_case": {"grid_h": 18, "grid_w": 24},
    "samples": len(rows),
    "exact_hits": sum(row["requested"] == row["observed"] for row in rows),
    "contexts_with_any_recorded_axis": sum(bool(row["recorded_draws"]) for row in rows),
    "contexts_using_any_override": sum(bool(row["overrides_used"]) for row in rows),
    "rows": rows,
}
print(json.dumps(report, indent=2, sort_keys=True))
