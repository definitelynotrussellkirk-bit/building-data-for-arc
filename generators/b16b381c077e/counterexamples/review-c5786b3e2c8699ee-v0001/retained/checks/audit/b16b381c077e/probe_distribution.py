#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEN_PATH = ROOT / "repo/generators/b16b381c077e/generator.py"
OUT = ROOT / "checks/audit/b16b381c077e/probe.json"

spec = importlib.util.spec_from_file_location("audit_b16_generator", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

per_band = 200
seed_base = 160000
bands = {}
for band_index, band in enumerate(("easy", "medium", "hard")):
    panel_counts = Counter()
    kind_counts = Counter()
    profile_hits = 0
    errors = []
    for i in range(per_band):
        grid = mod.generate(seed_base + band_index, i, difficulty=band)
        check = mod.self_check(grid, difficulty=band)
        if check:
            errors.append({"sample_index": i, "errors": check})
        observed = mod.observe_overrides(grid)
        panel_counts[str(observed["panel"])] += 1
        kind_counts[observed["kind"]] += 1
        # Canonical dimensions and palette count from the battery report:
        # 3x11 or 4x14, with colors {0, one panel color, divider, query color}.
        colors = {value for row in grid for value in row}
        if (len(grid), len(grid[0]), len(colors)) in {(3, 11, 4), (4, 14, 4)}:
            profile_hits += 1
    bands[band] = {
        "draws": per_band,
        "seed": seed_base + band_index,
        "panel_counts": dict(sorted(panel_counts.items())),
        "kind_counts": dict(sorted(kind_counts.items())),
        "canonical_profile_hits": profile_hits,
        "self_check_failures": errors,
    }

invalid_difficulty = {"value": "extreme", "accepted": False, "observed": None, "error": None}
try:
    grid = mod.generate(160999, 0, difficulty="extreme")
    invalid_difficulty["accepted"] = True
    invalid_difficulty["observed"] = mod.observe_overrides(grid)
    invalid_difficulty["self_check"] = mod.self_check(grid, difficulty="extreme")
except Exception as exc:  # evidence, not a production path
    invalid_difficulty["error"] = f"{type(exc).__name__}: {exc}"

report = {
    "schema": "arc-audit-probe-v1",
    "task_id": mod.TASK_ID,
    "version": mod.VERSION,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash": mod.RULE_HASH,
    "bands": bands,
    "invalid_difficulty": invalid_difficulty,
    "conclusion": {
        "hard_has_canonical_profile_support": bands["hard"]["canonical_profile_hits"] > 0,
        "hard_panel_values": sorted(bands["hard"]["panel_counts"]),
        "all_transform_kinds_seen_each_band": all(len(v["kind_counts"]) == 7 for v in bands.values()),
    },
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
