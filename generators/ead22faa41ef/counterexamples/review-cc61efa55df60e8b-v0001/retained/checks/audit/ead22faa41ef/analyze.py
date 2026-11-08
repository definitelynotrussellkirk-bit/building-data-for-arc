#!/usr/bin/env python3
"""Verify the all-3/all-2 shortcut against retained Racket outputs."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
inputs = json.loads((HERE / "input.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
official = [row["output"] for row in racket["results"]]


def rival(grid):
    return [[8 if v == 3 else 0 if v == 2 else v for v in row] for row in grid]

rival_outputs = [rival(grid) for grid in inputs]
matches = [a == b for a, b in zip(rival_outputs, official)]
diffs = []
for q, (expected, actual) in enumerate(zip(official, rival_outputs)):
    cells = []
    for r, row in enumerate(expected):
        for c, value in enumerate(row):
            if value != actual[r][c]:
                cells.append({"row": r, "col": c, "official": value, "rival": actual[r][c], "input": inputs[q][r][c]})
    diffs.append(cells)

(HERE / "rival.json").write_text(json.dumps(rival_outputs, indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": "ead22faa41ef",
    "finding": "three-demo lesson admits replace-every-3-and-2 shortcut",
    "source_sha256": racket["generator_sha256"],
    "rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "generator_call": {"seed": 3351, "sample_indices": [0, 1, 2, 3], "difficulty": "medium", "overrides": {}},
    "demo_indices": [0, 1, 2],
    "query_index": 3,
    "rival_name": "replace_all_3_with_8_and_all_2_with_0",
    "rival_matches_each_case": matches,
    "rival_matches_all_demonstrations": all(matches[:3]),
    "query_differs": not matches[3],
    "query_differing_cell_count": len(diffs[3]),
    "query_differing_cells": diffs[3],
    "all_inputs_pass_generator_self_check": True,
    "documented_domain": "medium defaults, sequential sample indices 0..3",
    "racket_apply": {"command": racket["command"], "cwd": racket["cwd"]},
    "evidence": {"input": "input.json", "generation": "generation.json", "racket": "racket.json", "rival": "rival.json"},
}
(HERE / "counterexample.json").write_text(json.dumps(report, indent=2) + "\n")
assert report["rival_matches_all_demonstrations"]
assert report["query_differs"]
assert report["query_differing_cell_count"] == 3
print(json.dumps({k: report[k] for k in ("task_id", "source_sha256", "rule_hash", "rival_matches_all_demonstrations", "query_differs", "query_differing_cell_count")}, indent=2))
