#!/usr/bin/env python3
"""Reproduce the exact-isolated-triple shortcut finding for task 994f16f93144."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
sys.path[:0] = [str(REPO / "shared/runtime")]

module_path = REPO / "generators/994f16f93144/generator.py"
spec = importlib.util.spec_from_file_location("probe_994f16f93144", module_path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

with (REPO / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
    canonical = next(
        json.loads(line)
        for line in handle
        if json.loads(line).get("task_id") == module.TASK_ID
    )
pairs = list(canonical["train"]) + list(canonical["test"])
rival = module.SEMANTIC_RIVALS["isolated_exact_triples_only"]
print("canonical authority matches:", sum(module.rule_mirror(p["input"]) == p["output"] for p in pairs), "/", len(pairs))
print("canonical rival matches:", sum(rival(p["input"]) == p["output"] for p in pairs), "/", len(pairs))

for band_index, band in enumerate(("easy", "medium", "hard")):
    totals = {"valid": 0, "strict": 0, "overlap_witness": 0, "rival_disagrees": 0}
    for index in range(200):
        grid = module.generate(100_000 + 1_000 * band_index + index, index, difficulty=band)
        facts = module._analyze_scene(grid)
        totals["valid"] += not facts["errors"]
        totals["strict"] += not module.strict_canonical_like(grid)
        totals["overlap_witness"] += bool(facts["overlapping_target_cells"])
        totals["rival_disagrees"] += rival(grid) != module.rule_mirror(grid)
    print(band, totals)

witness = [[0] * 7 for _ in range(7)]
for index in range(1, 5):
    witness[index][index] = 4
print("witness input:", json.dumps(witness, separators=(",", ":")))
print("intended output:", json.dumps(module.rule_mirror(witness), separators=(",", ":")))
print("rival output:", json.dumps(rival(witness), separators=(",", ":")))
