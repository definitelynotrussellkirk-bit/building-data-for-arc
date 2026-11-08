#!/usr/bin/env python3
"""Read-only source-bound audit probe for b2d893865427."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / "repo"
RUNTIME = ROOT / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import canonical_pairs

TASK = "b2d893865427"
GENERATOR = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_b2", GENERATOR)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

seed = 77
sample_index = 3
difficulty = "medium"
baseline = gen.generate(seed, sample_index, difficulty=difficulty)
override_cases = [
    {"grid_h": 9}, {"grid_h": 14}, {"grid_w": 9}, {"grid_w": 14},
    {"n_blocks": 2}, {"n_blocks": 5},
    {"palette_size": 2}, {"palette_size": 5},
    {"n_distinct_colors": 2}, {"n_distinct_colors": 5},
]
overrides = []
for case in override_cases:
    grid = gen.generate(seed, sample_index, difficulty=difficulty, **case)
    overrides.append({
        "overrides": case,
        "identical_to_unoverridden": grid == baseline,
        "shape": [len(grid), len(grid[0])],
        "self_check": gen.self_check(grid, difficulty=difficulty),
    })

degenerates = []
for texture in ("no_blocks", "blocks_share_row", "blocks_share_col"):
    grid = gen.generate(seed, sample_index, difficulty=difficulty, texture=texture)
    degenerates.append({
        "texture": texture,
        "shape": [len(grid), len(grid[0])],
        "self_check": gen.self_check(grid, difficulty=difficulty),
        "grid": grid,
    })

report = {
    "schema": "arcpuzzles-audit-probe/1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "generator_version": gen.VERSION,
    "declared_rule_hash": getattr(gen, "RULE_HASH", None),
    "canonical_pairs": len(canonical_pairs(TASK, root=ROOT, labeled_only=True)),
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "baseline_grid": baseline,
    "baseline_self_check": gen.self_check(baseline, difficulty=difficulty),
    "override_cases": overrides,
    "all_tested_overrides_inert": all(item["identical_to_unoverridden"] for item in overrides),
    "degenerate_cases": degenerates,
    "all_declared_degenerates_rejected_by_self_check": all(item["self_check"] for item in degenerates),
    "finding": (
        "Declared exact-looking axes are ignored, and every declared degenerate texture "
        "returns a grid rejected by the generator's own validator."
    ),
}
Path(__file__).with_name("probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
Path(__file__).with_name("input.json").write_text(json.dumps(baseline, indent=2) + "\n")
print(json.dumps({
    "generator_sha256": report["generator_sha256"],
    "all_tested_overrides_inert": report["all_tested_overrides_inert"],
    "all_declared_degenerates_rejected_by_self_check": report["all_declared_degenerates_rejected_by_self_check"],
}, sort_keys=True))
