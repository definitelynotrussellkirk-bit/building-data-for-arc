#!/usr/bin/env python3
"""Reproduce a 3-demo lesson where D4 congruence survives, then fails on query."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "2602c3d31d21"
SEED = 8
SAMPLE_INDICES = [0, 1, 2, 3]
DIFFICULTY = "easy"
OUT = Path(__file__).resolve().parent


def congruence_rival(module, grid):
    info = module._analysis(grid)
    colors = info["key_colors"]
    signatures = [shape["congruence"] for shape in info["shapes"]]
    total = (len(colors) + 1) * 3 - 1
    output = [[0 for _ in range(total)] for _ in range(total)]
    for row in range(total):
        for col in range(total):
            block_row, local_row = divmod(row, 3)
            block_col, local_col = divmod(col, 3)
            if local_row == 2 or local_col == 2:
                continue
            if block_row == 0 and block_col > 0:
                output[row][col] = colors[block_col - 1]
            elif block_col == 0 and block_row > 0:
                output[row][col] = colors[block_row - 1]
            elif block_row > 0 and block_col > 0 and block_row != block_col:
                output[row][col] = (
                    2 if signatures[block_row - 1] == signatures[block_col - 1] else 5
                )
    return output


def main():
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=OUT.parents[2] / "repo")
    grids = [module.generate(SEED, index, difficulty=DIFFICULTY) for index in SAMPLE_INDICES]
    validator = [module.self_check(grid, difficulty=DIFFICULTY) for grid in grids]
    intended = [module.rule_mirror(grid) for grid in grids]
    rival = [congruence_rival(module, grid) for grid in grids]
    profiles = [module.observe_overrides(grid)["scene_profile"] for grid in grids]
    matches = [left == right for left, right in zip(intended, rival)]
    assert validator == [[], [], [], []]
    assert matches == [True, True, True, False]
    assert profiles[-1] == "collision_different_size"

    (OUT / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
    (OUT / "rival_outputs.json").write_text(json.dumps(rival, indent=2) + "\n")
    generation = {
        "schema": "arcpuzzles-audit-generation-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha,
        "seed": SEED,
        "sample_indices": SAMPLE_INDICES,
        "difficulty": DIFFICULTY,
        "overrides": {},
        "profiles": profiles,
        "validator_messages": validator,
        "rival_matches_python_mirror": matches,
        "input_sha256": hashlib.sha256((OUT / "input.json").read_bytes()).hexdigest(),
    }
    (OUT / "generation.json").write_text(json.dumps(generation, indent=2) + "\n")
    print(json.dumps(generation, indent=2))


if __name__ == "__main__":
    main()
