#!/usr/bin/env python3
"""Verify the every-uniform-line rival against retained Racket outputs."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
inputs = json.loads((HERE / "input.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
base_outputs = [row["output"] for row in racket["results"]]


def every_uniform_line(grid):
    n = len(grid)
    urows = [r for r in range(n) if len(set(grid[r])) == 1]
    ucols = [c for c in range(n) if len({grid[r][c] for r in range(n)}) == 1]
    out = [[0] * (n * n) for _ in range(n * n)]
    for br in range(n):
        for bc in range(n):
            if br not in urows and bc not in ucols:
                continue
            for r in range(n):
                for c in range(n):
                    out[br * n + r][bc * n + c] = grid[r][c]
    return out

rival_outputs = [every_uniform_line(grid) for grid in inputs]
matches = [a == b for a, b in zip(rival_outputs, base_outputs)]
diffs = []
for q, (expected, actual) in enumerate(zip(base_outputs, rival_outputs)):
    cells = []
    for r, row in enumerate(expected):
        for c, value in enumerate(row):
            if value != actual[r][c]:
                cells.append({"row": r, "col": c, "official": value, "rival": actual[r][c]})
    diffs.append(cells)

(HERE / "rival.json").write_text(json.dumps(rival_outputs, indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": "2082a4577cff",
    "finding": "three-demo lesson admits every-uniform-line shortcut",
    "source_sha256": racket["generator_sha256"],
    "rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "generator_call": {"seed": 20, "sample_indices": [0, 1, 2, 3], "difficulty": "easy", "overrides": {}},
    "demo_indices": [0, 1, 2],
    "query_index": 3,
    "rival_name": "tile_at_every_uniform_row_or_column",
    "rival_matches_each_case": matches,
    "rival_matches_all_demonstrations": all(matches[:3]),
    "query_differs": not matches[3],
    "query_differing_cell_count": len(diffs[3]),
    "query_differing_cells": diffs[3],
    "all_inputs_pass_generator_self_check": True,
    "documented_domain": "easy defaults, sequential sample indices 0..3",
    "racket_apply": {"command": racket["command"], "cwd": racket["cwd"]},
    "evidence": {"input": "input.json", "generation": "generation.json", "racket": "racket.json", "rival": "rival.json"},
}
(HERE / "counterexample.json").write_text(json.dumps(report, indent=2) + "\n")
assert report["rival_matches_all_demonstrations"]
assert report["query_differs"]
assert report["query_differing_cell_count"] == 27
print(json.dumps({k: report[k] for k in ("task_id", "source_sha256", "rule_hash", "rival_matches_all_demonstrations", "query_differs", "query_differing_cell_count")}, indent=2))
