#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "23c3ab5fa55f"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
apply = json.loads((HERE / "racket.json").read_text())
pre = json.loads((HERE / "probe-pre.json").read_text())


def duplicate_removal(grid):
    width = len(grid[0])
    out = []
    for row in grid:
        seen = set()
        kept = []
        for value in row:
            if value != 0 and value not in seen:
                seen.add(value)
                kept.append(value)
        out.append(kept + [0] * (width - len(kept)))
    return out

canonical_checks = []
for pair in canonical_pairs(TASK_ID, root=ROOT):
    rival = duplicate_removal(pair["input"])
    canonical_checks.append(rival == pair["output"])

results = apply["results"]
lesson_matches = []
for row in results:
    rival = duplicate_removal(row["input"])
    lesson_matches.append(rival == row["output"])
query = results[-1]
rival_query = duplicate_removal(query["input"])
differences = []
for r, (expected_row, rival_row) in enumerate(zip(query["output"], rival_query)):
    for c, (expected, rival) in enumerate(zip(expected_row, rival_row)):
        if expected != rival:
            differences.append({"row": r, "column": c, "canonical": expected, "rival": rival})

payload = {
    "schema": "arcpuzzles-audit-verification-v1",
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA,
    "executed_rule_hash": apply["executed_rule_hash"],
    "rule_hash_matches_catalog": apply["rule_hash_matches_catalog"],
    "canonical_duplicate_removal_matches": canonical_checks,
    "canonical_fit_count": sum(canonical_checks),
    "canonical_pair_count": len(canonical_checks),
    "lesson_duplicate_removal_matches": lesson_matches,
    "demonstration_fit_count": sum(lesson_matches[:-1]),
    "demonstration_count": len(lesson_matches) - 1,
    "query_differs": not lesson_matches[-1],
    "query_differences": differences,
    "query_self_check": query.get("generator_domain"),
    "override_results": pre["override_results"],
}
(HERE / "verification.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
counterexample = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": TASK_ID,
    "generator_sha256": SOURCE_SHA,
    "rule_hash": apply["executed_rule_hash"],
    "seed": 26,
    "sample_index": 4,
    "difficulty": "easy",
    "input": query["input"],
    "canonical_output": query["output"],
    "rival_name": "remove_duplicate_colors_within_each_row_then_compact_left",
    "rival_output": rival_query,
    "differing_cells": differences,
    "domain_status": query.get("generator_domain"),
    "command": apply["command"],
    "cwd": apply["cwd"],
}
(HERE / "counterexample.json").write_text(json.dumps(counterexample, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "canonical_fit": [sum(canonical_checks), len(canonical_checks)],
    "demo_fit": [sum(lesson_matches[:-1]), len(lesson_matches)-1],
    "query_differs": not lesson_matches[-1],
    "differing_cells": len(differences),
    "generator_sha256": SOURCE_SHA,
}, sort_keys=True))
