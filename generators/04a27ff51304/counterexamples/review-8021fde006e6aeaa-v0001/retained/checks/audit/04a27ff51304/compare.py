#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_ID = "04a27ff51304"


def run_len_nonzero(grid, r, c, dr, dc):
    if grid[r][c] == 0:
        return 0
    h, w = len(grid), len(grid[0])
    n = 1
    rr, cc = r + dr, c + dc
    while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 0:
        n += 1
        rr += dr
        cc += dc
    rr, cc = r - dr, c - dc
    while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 0:
        n += 1
        rr -= dr
        cc -= dc
    return n


def rival(grid):
    return [
        [
            8 if value != 0
            and run_len_nonzero(grid, r, c, 0, 1) >= 3
            and run_len_nonzero(grid, r, c, 1, 0) >= 3
            else 0
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]

inputs = json.loads((HERE / "input.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
authority = [row["output"] for row in racket["results"]]
rival_outputs = [rival(grid) for grid in inputs]
agreement = [a == b for a, b in zip(authority, rival_outputs)]
assert agreement == [True, True, True, False], agreement
changed = [
    [r, c]
    for r, row in enumerate(authority[3])
    for c, value in enumerate(row)
    if value != rival_outputs[3][r][c]
]
assert len(changed) == 1
report = {
    "schema": "audit-teaching-ambiguity-v1",
    "task_id": TASK_ID,
    "generator_sha256": racket["generator_sha256"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "seed": 0,
    "sample_indices": [0, 1, 2, 3],
    "difficulty": None,
    "rival": "paint occupancy crossings, ignoring whether horizontal and vertical runs have the same color",
    "rival_agrees_with_authority": agreement,
    "all_demonstrations_fit": all(agreement[:3]),
    "query_differs": not agreement[3],
    "query_differing_cells": changed,
    "authority_query_output": authority[3],
    "rival_query_output": rival_outputs[3],
    "all_inputs_pass_self_check": True,
    "inputs": "input.json",
    "racket": "racket.json",
    "command": {
        "cwd": "packet_root",
        "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK_ID, "--input", "../checks/audit/04a27ff51304/input.json", "--out", "../checks/audit/04a27ff51304/racket.json"],
    },
}
(HERE / "rival-output.json").write_text(json.dumps({"outputs": rival_outputs}, indent=2) + "\n")
(HERE / "shortcut-repro.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
