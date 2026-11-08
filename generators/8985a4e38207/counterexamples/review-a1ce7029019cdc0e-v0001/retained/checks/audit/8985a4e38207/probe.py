#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "8985a4e38207"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
HERE = Path(__file__).resolve().parent
GRID = json.loads((HERE / "input.json").read_text())
RACKET = json.loads((HERE / "racket.json").read_text())
RACKET_OUTPUT = RACKET["results"][0]["output"]


def shared_marker_column_rival(grid):
    template = {c for c, value in enumerate(grid[0]) if value != 0}
    counts = {}
    for row in grid[1:]:
        for col, value in enumerate(row):
            if value != 0 and col not in template:
                counts[col] = counts.get(col, 0) + 1
    chosen = max(counts, key=lambda col: (counts[col], col)) if counts else None
    output = [row[:] for row in grid]
    if chosen is None:
        return output
    for r in range(1, len(grid)):
        if grid[r][chosen] != 0 and chosen not in template:
            for c in template:
                output[r][c] = 2
    return output


def marker_columns(grid):
    template = {c for c, value in enumerate(grid[0]) if value != 0}
    return sorted({
        c
        for row in grid[1:]
        for c, value in enumerate(row)
        if value != 0 and c not in template
    })


canonical = canonical_pairs(TASK_ID, root=ROOT)
canonical_fit = [shared_marker_column_rival(pair["input"]) == pair["output"] for pair in canonical]
sweep = []
for difficulty in ("easy", "medium", "hard"):
    for seed in range(100):
        grid = GEN.generate(seed, seed * 7, difficulty=difficulty)
        sweep.append({
            "difficulty": difficulty,
            "seed": seed,
            "marker_columns": marker_columns(grid),
            "self_check": GEN.self_check(grid),
        })

paired_axis = []
for seed in range(32):
    false_grid = GEN.generate(seed, 11, difficulty="medium", asymmetry_force=False)
    true_grid = GEN.generate(seed, 11, difficulty="medium", asymmetry_force=True)
    paired_axis.append({
        "seed": seed,
        "identical": false_grid == true_grid,
        "false_sha256": hashlib.sha256(json.dumps(false_grid, separators=(",", ":")).encode()).hexdigest(),
        "true_sha256": hashlib.sha256(json.dumps(true_grid, separators=(",", ":")).encode()).hexdigest(),
    })

rival_output = shared_marker_column_rival(GRID)
disagreements = [
    [r, c]
    for r in range(len(GRID))
    for c in range(len(GRID[0]))
    if RACKET_OUTPUT[r][c] != rival_output[r][c]
]
report = {
    "schema": "arcpuzzles-audit-shared-marker-shortcut-v1",
    "task_id": TASK_ID,
    "generator_source": str(SOURCE.relative_to(ROOT)),
    "generator_sha256": SOURCE_SHA256,
    "generator_version": GEN.VERSION,
    "rule_hash": RACKET["executed_rule_hash"],
    "rule_text_sha256": RACKET["rule_text_sha256"],
    "finding": "all generated marker rows share one marker column, admitting a narrower shared-column rival; advertised asymmetry_force is also ignored",
    "canonical_pairs": len(canonical),
    "canonical_rival_fit": canonical_fit,
    "all_canonical_pairs_fit": all(canonical_fit),
    "generated_sweep": {
        "samples": len(sweep),
        "bands": ["easy", "medium", "hard"],
        "seed_range": [0, 99],
        "all_self_checks_pass": all(not item["self_check"] for item in sweep),
        "all_have_at_most_one_marker_column": all(len(item["marker_columns"]) <= 1 for item in sweep),
        "max_marker_columns": max(len(item["marker_columns"]) for item in sweep),
    },
    "ignored_axis_probe": {
        "axis": "asymmetry_force",
        "pairs": len(paired_axis),
        "all_paired_outputs_identical": all(item["identical"] for item in paired_axis),
        "cases": paired_axis,
    },
    "counterexample": {
        "input": GRID,
        "self_check": GEN.self_check(GRID),
        "canonical_racket_output": RACKET_OUTPUT,
        "rival_output": rival_output,
        "disagreement_coordinates": disagreements,
        "racket_receipt": "checks/audit/8985a4e38207/racket.json",
    },
    "scope": "four canonical pairs, 300 generated inputs, 32 paired exact-axis calls; no target files edited",
}
(HERE / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "all_canonical_pairs_fit": report["all_canonical_pairs_fit"],
    "generated_samples": report["generated_sweep"]["samples"],
    "all_generated_share_one_marker_column": report["generated_sweep"]["all_have_at_most_one_marker_column"],
    "asymmetry_force_all_identical": report["ignored_axis_probe"]["all_paired_outputs_identical"],
    "counterexample_self_check": report["counterexample"]["self_check"],
    "disagreements": disagreements,
}, sort_keys=True))
