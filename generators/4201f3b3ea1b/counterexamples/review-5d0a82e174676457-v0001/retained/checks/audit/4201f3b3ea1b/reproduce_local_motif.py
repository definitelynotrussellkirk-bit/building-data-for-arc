#!/usr/bin/env python3
"""Reproduce a local-motif shortcut surviving four production demonstrations."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK = "4201f3b3ea1b"
GENERATOR = Path("generators") / TASK / "generator.py"
OUT = Path("../checks/audit") / TASK
SEED = 1
START = 1
DIFFICULTY = "easy"
DEMONSTRATIONS = 4


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def local_motif_rival(grid: list[list[int]]) -> list[list[int]]:
    """Stamp only motif cells within Chebyshev radius two of the first 5."""
    height, width = len(grid), len(grid[0])
    source = next(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    )
    anchors = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 6
    ]
    motif = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 5, 6)
        and max(abs(row - source[0]), abs(col - source[1])) <= 2
    ]
    output = [row[:] for row in grid]
    for anchor_row, anchor_col in anchors:
        for row, col, color in motif:
            target_row = anchor_row + row - source[0]
            target_col = anchor_col + col - source[1]
            if 0 <= target_row < height and 0 <= target_col < width:
                output[target_row][target_col] = color
    return output


def main() -> None:
    module = load_generator()
    OUT.mkdir(parents=True, exist_ok=True)
    pairs = []
    for sample_index in range(START, START + DEMONSTRATIONS + 1):
        grid = module.generate(SEED, sample_index, difficulty=DIFFICULTY)
        intended = module.rule_mirror(grid)
        rival = local_motif_rival(grid)
        pairs.append(
            {
                "seed": SEED,
                "sample_index": sample_index,
                "difficulty": DIFFICULTY,
                "scene_profile": module.observe_overrides(grid)["scene_profile"],
                "input": grid,
                "intended_output": intended,
                "local_motif_output": rival,
                "rival_matches": rival == intended,
            }
        )

    demos = pairs[:DEMONSTRATIONS]
    query = pairs[DEMONSTRATIONS]
    summary = {
        "schema": "arc-audit-reproducer-v1",
        "task_id": TASK,
        "generator_path": str(GENERATOR),
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "declared_rule_hash": module.RULE_HASH,
        "seed": SEED,
        "start_index": START,
        "difficulty": DIFFICULTY,
        "demonstration_count": DEMONSTRATIONS,
        "profiles": [pair["scene_profile"] for pair in pairs],
        "rival": {
            "name": "local_motif_radius_two",
            "description": (
                "Treat only non-{0,5,6} cells within Chebyshev radius 2 of "
                "the first 5 as the motif, then stamp them normally."
            ),
            "fits_all_demonstrations": all(pair["rival_matches"] for pair in demos),
            "demonstration_fit_vector": [pair["rival_matches"] for pair in demos],
            "changes_query_answer": not query["rival_matches"],
        },
        "command": [
            "python3",
            "review.py",
            "run",
            "python3",
            "../checks/audit/4201f3b3ea1b/reproduce_local_motif.py",
        ],
        "effective_cwd": "WORK/repo",
    }
    if not summary["rival"]["fits_all_demonstrations"]:
        raise AssertionError(summary)
    if not summary["rival"]["changes_query_answer"]:
        raise AssertionError(summary)

    (OUT / "local_motif_probe.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT / "local_motif_lesson.json").write_text(
        json.dumps({"summary": summary, "pairs": pairs}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
