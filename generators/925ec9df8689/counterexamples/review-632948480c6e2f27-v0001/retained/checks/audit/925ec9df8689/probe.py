#!/usr/bin/env python3
"""Reproduce the decoration-preservation curriculum gap in 925ec9df8689."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "925ec9df8689"
REPO = Path.cwd()
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
EVIDENCE = REPO.parent / "checks" / "audit" / TASK_ID

spec = importlib.util.spec_from_file_location("audit_925", SOURCE)
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def intended(grid):
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height - 1):
        for col in range(width - 1):
            coords = (
                (row, col), (row, col + 1),
                (row + 1, col), (row + 1, col + 1),
            )
            values = [grid[r][c] for r, c in coords]
            zeros = [(r, c) for r, c in coords if grid[r][c] == 0]
            if values.count(4) == 3 and len(zeros) == 1:
                r, c = zeros[0]
                out[r][c] = 2
    return out


def erase_decorations_rival(grid):
    out = intended(grid)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] not in (0, 4):
                out[row][col] = 0
    return out


input_grid = json.loads((EVIDENCE / "input.json").read_text())
receipt = json.loads((EVIDENCE / "racket.json").read_text())
racket_output = receipt["results"][0]["output"]
assert GEN.self_check(input_grid) == []
assert intended(input_grid) == racket_output
rival_output = erase_decorations_rival(input_grid)
differences = [
    [row, col, racket_output[row][col], rival_output[row][col]]
    for row in range(len(input_grid))
    for col in range(len(input_grid[0]))
    if racket_output[row][col] != rival_output[row][col]
]
assert differences == [[3, 0, 6, 0]]

bands = {}
for band in (None, "easy", "medium", "hard"):
    palette = set()
    invalid = 0
    rival_disagreements = 0
    unique = set()
    for index in range(250):
        grid = GEN.generate(925000 + index, index, difficulty=band)
        palette.update(value for row in grid for value in row)
        invalid += bool(GEN.self_check(grid, difficulty=band))
        rival_disagreements += erase_decorations_rival(grid) != intended(grid)
        unique.add(json.dumps(grid, separators=(",", ":")))
    assert palette <= {0, 4}
    assert invalid == 0
    assert rival_disagreements == 0
    bands[str(band)] = {
        "samples": 250,
        "unique_inputs": len(unique),
        "observed_palette": sorted(palette),
        "self_check_failures": invalid,
        "rival_disagreements": rival_disagreements,
    }

(EVIDENCE / "rival-output.json").write_text(json.dumps(rival_output, indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": TASK_ID,
    "generator_version": GEN.VERSION,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "executed_rule_hash": receipt["executed_rule_hash"],
    "input_is_validator_lawful": True,
    "documented_domain_feature": "non-yellow decoration cells preserved unchanged",
    "rival": "complete yellow L-windows, but erase every pre-existing non-0/non-4 decoration",
    "differing_cells_zero_based": differences,
    "generated_pool": bands,
    "finding": (
        "The generator emitted no decoration color in 1000 checked samples, so the rival "
        "fit the entire sampled synthetic pool while disagreeing with the selected Racket "
        "rule on a lawful documented-domain input."
    ),
    "evidence": {
        "input": "checks/audit/925ec9df8689/input.json",
        "racket": "checks/audit/925ec9df8689/racket.json",
        "rival_output": "checks/audit/925ec9df8689/rival-output.json",
    },
}
(EVIDENCE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
