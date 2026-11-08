#!/usr/bin/env python3
"""Reproduce a four-demo lesson where recolor-all survives, then fails on query."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "68b4181d35e1"
SEED = 1
SAMPLE_INDICES = [2, 3, 4, 5, 6]
DIFFICULTY = "easy"
OUT = Path(__file__).resolve().parent


def recolor_all_rival(grid):
    out = [row[:] for row in grid]
    for row in out:
        header = row[0]
        marker_cols = [col for col, value in enumerate(row[1:], start=1) if value == 1]
        if header not in (0, 1) and marker_cols:
            row[0] = 0
            for col in marker_cols:
                row[col] = header
    return out


def main():
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=OUT.parents[2] / "repo")
    grids = [module.generate(SEED, index, difficulty=DIFFICULTY) for index in SAMPLE_INDICES]
    validator = [module.self_check(grid, difficulty=DIFFICULTY) for grid in grids]
    rivals = [recolor_all_rival(grid) for grid in grids]
    assert validator == [[], [], [], [], []]
    (OUT / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
    (OUT / "rival_outputs.json").write_text(json.dumps(rivals, indent=2) + "\n")
    generation = {
        "schema": "arcpuzzles-audit-generation-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha,
        "seed": SEED,
        "sample_indices": SAMPLE_INDICES,
        "difficulty": DIFFICULTY,
        "overrides": {},
        "validator_messages": validator,
        "input_sha256": hashlib.sha256((OUT / "input.json").read_bytes()).hexdigest(),
    }
    (OUT / "generation.json").write_text(json.dumps(generation, indent=2) + "\n")
    print(json.dumps(generation, indent=2))


if __name__ == "__main__":
    main()
