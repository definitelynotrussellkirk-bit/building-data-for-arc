#!/usr/bin/env python3
"""Verify a concrete all-green-to-cyan shortcut against Racket outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
probe = json.loads((ROOT / "probe.json").read_text())
receipt = json.loads((ROOT / "racket.json").read_text())
inputs = probe["inputs"]
results = receipt["results"]
assert len(inputs) == len(results) == 4


def rival(grid: list[list[int]]) -> list[list[int]]:
    return [[8 if value == 3 else 0 if value == 1 else value for value in row] for row in grid]

rows = []
for index, (grid, result) in enumerate(zip(inputs, results)):
    intended = result["output"]
    guess = rival(grid)
    differing = [
        {"row": r, "column": c, "rival": guess[r][c], "intended": intended[r][c]}
        for r in range(len(grid))
        for c in range(len(grid[r]))
        if guess[r][c] != intended[r][c]
    ]
    rows.append(
        {
            "index": index,
            "role": "demo" if index < 3 else "query",
            "rival_matches_intended": not differing,
            "differing_cells": differing,
        }
    )

report = {
    "schema": "arcpuzzles-audit-shortcut-verification-v1",
    "task_id": probe["task_id"],
    "generator_sha256": receipt["generator_sha256"],
    "executed_rule_hash": receipt["executed_rule_hash"],
    "rule_text_sha256": receipt["rule_text_sha256"],
    "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
    "lesson": probe["lesson"],
    "shortcut": "erase the blue (1) template and replace every green (3) cell with cyan (8), without comparing shapes",
    "rows": rows,
    "all_demos_fit": all(row["rival_matches_intended"] for row in rows[:3]),
    "query_diverges": not rows[3]["rival_matches_intended"],
    "query_difference_count": len(rows[3]["differing_cells"]),
    "inputs_sha256": hashlib.sha256((ROOT / "inputs.json").read_bytes()).hexdigest(),
    "racket_receipt_sha256": hashlib.sha256((ROOT / "racket.json").read_bytes()).hexdigest(),
}
assert report["all_demos_fit"]
assert report["query_diverges"]
(ROOT / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
