"""Independent probes for task 510b12f6a12a.

This module deliberately does not import implementation helpers from generator.py.
It mirrors only the public puzzle statement: color-2 emitters on the top edge
cast downward, color-1 emitters on the left edge cast rightward, color-5 cells
stop a ray, and surviving ray intersections are painted color 6 on a blank grid.
"""
from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

TASK_ID = "510b12f6a12a"
GENERATOR_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = GENERATOR_HOME.parents[1]


def normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def canonical_pairs():
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs = list(row.get("train") or [])
            test = row.get("test")
            if isinstance(test, list):
                pairs.extend(test)
            elif isinstance(test, dict):
                pairs.append(test)
            return [
                {
                    "input": normalize_grid(pair["input"]),
                    "output": normalize_grid(pair["output"]),
                }
                for pair in pairs
            ]
    raise AssertionError(f"canonical task {TASK_ID} not found")


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = path or os.environ.get("GENERATOR_UNDER_TEST")
    if not selected:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    selected_path = Path(selected)
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", selected_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {selected_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def beam_output(grid, *, vertical_limit: int | None = None,
                horizontal_limit: int | None = None,
                ignore_blockers: bool = False):
    """Independent rule oracle, with optional rival restrictions."""
    source = normalize_grid(grid)
    h, w = len(source), len(source[0])
    vertical = [c for c in range(1, w) if source[0][c] == 2]
    horizontal = [r for r in range(1, h) if source[r][0] == 1]
    if vertical_limit is not None:
        vertical = vertical[:vertical_limit]
    if horizontal_limit is not None:
        horizontal = horizontal[:horizontal_limit]

    vertical_reach: set[tuple[int, int]] = set()
    for c in vertical:
        for r in range(1, h):
            if not ignore_blockers and source[r][c] == 5:
                break
            vertical_reach.add((r, c))

    horizontal_reach: set[tuple[int, int]] = set()
    for r in horizontal:
        for c in range(1, w):
            if not ignore_blockers and source[r][c] == 5:
                break
            horizontal_reach.add((r, c))

    output = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in vertical_reach & horizontal_reach:
        output[r][c] = 6
    return output


def observed(grid):
    source = normalize_grid(grid)
    return {
        "grid_h": len(source),
        "grid_w": len(source[0]),
        "n_v": sum(value == 2 for value in source[0][1:]),
        "n_h": sum(row[0] == 1 for row in source[1:]),
        "n_blockers": sum(value == 5 for row in source for value in row),
    }


def differing_cells(a, b) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, (row_a, row_b) in enumerate(zip(a, b))
        for c, (value_a, value_b) in enumerate(zip(row_a, row_b))
        if value_a != value_b
    ]


def functional_blocker(grid) -> bool:
    return bool(differing_cells(beam_output(grid), beam_output(grid, ignore_blockers=True)))


def extra_emitter_counterexample(grid) -> bool:
    return bool(
        differing_cells(
            beam_output(grid),
            beam_output(grid, vertical_limit=2, horizontal_limit=2),
        )
    )
