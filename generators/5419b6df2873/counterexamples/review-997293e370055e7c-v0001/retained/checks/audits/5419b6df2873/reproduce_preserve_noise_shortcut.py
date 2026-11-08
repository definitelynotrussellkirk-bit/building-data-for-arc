#!/usr/bin/env python3
"""Reproduce a 3-demo ambiguity in unmodified generator 5419b6df2873."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "5419b6df2873"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3] / "repo"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
OUT = HERE.parent

spec = importlib.util.spec_from_file_location("audit_5419", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def intended(grid):
    h, w = len(grid), len(grid[0])
    output = [[0] * w for _ in range(h)]
    for col, color in enumerate(grid[0]):
        if color:
            for row in range(h):
                output[row][col] = color
    return output


def preserve_noise_rival(grid):
    output = [row[:] for row in grid]
    for col, color in enumerate(grid[0]):
        if color:
            for row in range(len(grid)):
                output[row][col] = color
    return output


def unmarked_noise(grid):
    marked = {col for col, color in enumerate(grid[0]) if color}
    return [
        [row, col, grid[row][col]]
        for row in range(1, len(grid))
        for col in range(len(grid[0]))
        if col not in marked and grid[row][col] != 0
    ]

band, seed, start = "easy", 1, 9
grids = [module.generate(seed, start + offset, difficulty=band) for offset in range(4)]
truth = [intended(grid) for grid in grids]
rival = [preserve_noise_rival(grid) for grid in grids]
fits = [candidate == answer for candidate, answer in zip(rival, truth)]
assert fits == [True, True, True, False], fits
assert len({json.dumps(grid) for grid in grids}) == 4
report = {
    "schema": "audit-5419b6df2873-preserve-noise-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "difficulty": band,
    "seed": seed,
    "sample_index_start": start,
    "lesson_policy": "first three sequential samples are demos; fourth is query",
    "rival": "copy the input, fill marker columns, and preserve all lower-row cells in unmarked columns",
    "rival_fits": fits,
    "unmarked_noise": [unmarked_noise(grid) for grid in grids],
    "inputs": grids,
    "diagnostic_intended_outputs": truth,
    "rival_outputs": rival,
    "limitations": [
        "Diagnostic intended outputs are independently reconstructed from the public task summary; racket-output.json is the authority replay.",
        "This is one exact sequential lesson, not an estimate of ambiguity frequency."
    ],
}
(OUT / "input.json").write_text(json.dumps({"inputs": grids}, indent=2) + "\n")
(OUT / "reproduction.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"generator_sha256": report["generator_sha256"], "rival_fits": fits, "unmarked_noise": report["unmarked_noise"]}, indent=2))
