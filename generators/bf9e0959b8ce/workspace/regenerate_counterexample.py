#!/usr/bin/env python3
"""Regenerate the retained single-source-line counterexample deterministically."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "bf9e0959b8ce"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
OUT = ROOT / "generators" / TASK_ID / "counterexamples" / "single-source-line.json"


def main() -> int:
    seed = 8675309
    sample_index = 0
    difficulty = "easy"
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    intended = GEN.rule_mirror(grid)
    shortcut = GEN.CANONICAL_SHORTCUTS["single_source_line"](grid)
    if intended == shortcut:
        raise AssertionError("fixed witness no longer distinguishes the shortcut")
    info = GEN._analysis(grid)
    if info["errors"]:
        raise AssertionError(info["errors"])
    coordinates = [
        dot[0] if info["orientation"] == "row" else dot[1]
        for dot in info["dots"]
    ]
    differing = [
        [r, c]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if intended[r][c] != shortcut[r][c]
    ]
    payload = {
        "schema": "bf9e0959b8ce-counterexample-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "generator_version": GEN.VERSION,
        "generator_source_sha256": SOURCE_SHA256,
        "shortcut": "single_source_line",
        "claim": (
            "Route only dots on the earliest densest source row/column; "
            "ignore source dots on other movement-axis lines."
        ),
        "canonical_fit": (
            "All six labeled canonical pairs place every source dot on one "
            "movement-axis line, so the shortcut equals the intended rule there."
        ),
        "generated_disagreement": (
            "This generated input spans multiple source lines, so the shortcut "
            "leaves some dots unmoved while the intended rule routes all dots."
        ),
        "orientation": info["orientation"],
        "source_motion_coordinates": coordinates,
        "distinct_source_lines": sorted(set(coordinates)),
        "differing_cells": differing,
        "input": grid,
        "intended_output": intended,
        "shortcut_output": shortcut,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(OUT.relative_to(ROOT)),
        "generator_source_sha256": SOURCE_SHA256,
        "generator_version": GEN.VERSION,
        "orientation": info["orientation"],
        "distinct_source_lines": sorted(set(coordinates)),
        "differing_cells": len(differing),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
