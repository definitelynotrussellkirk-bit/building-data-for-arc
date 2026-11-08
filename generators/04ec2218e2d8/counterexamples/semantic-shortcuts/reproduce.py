#!/usr/bin/env python3
"""Reproduce the retained bbox-fill semantic counterexample."""
from __future__ import annotations

import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "shared/runtime"))

from reviewer_support import load_selected_generator  # noqa: E402


def main() -> None:
    payload = json.loads((HERE / "bbox_fill_minimal.json").read_text())
    generator, _source, digest = load_selected_generator(
        payload["task_id"],
        root=REPO,
    )
    call = payload["reproduction"]
    grid = generator.generate(
        call["seed"],
        call["sample_index"],
        difficulty=call["difficulty"],
        **call["overrides"],
    )
    canonical = generator.rule_mirror(grid)
    rival = generator.SEMANTIC_RIVALS[payload["rival_name"]](grid)

    assert digest == payload["authority"]["generator_sha256"]
    assert grid == payload["input"]
    assert generator.self_check(grid) == []
    assert canonical == payload["canonical_output"]
    assert rival == payload["rival_output"]
    observed_differences = [
        {
            "row": row,
            "col": col,
            "canonical": canonical[row][col],
            "rival": rival[row][col],
        }
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if canonical[row][col] != rival[row][col]
    ]
    assert observed_differences == payload["differing_cells"]
    print(json.dumps({
        "status": "reproduced",
        "task_id": payload["task_id"],
        "signature": payload["signature"],
        "differing_cells": observed_differences,
    }, indent=2))


if __name__ == "__main__":
    main()
