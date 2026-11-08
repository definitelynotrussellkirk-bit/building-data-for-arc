"""Independent probes for ba5056d6102e review tests.

This module deliberately does not import helpers from the selected generator.
It derives the panel relation and expected outputs directly from visible grids.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Callable

TASK_ID = "ba5056d6102e"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def load_generator(path: str | os.PathLike[str] | None = None) -> ModuleType:
    source = Path(path) if path else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}_{source.stat().st_mtime_ns}", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    return [*row.get("train", []), *row.get("test", [])]


def split_panels(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    width = len(grid[0])
    dividers = [
        r for r, row in enumerate(grid)
        if len(row) == width and all(value == 5 for value in row)
    ]
    if len(dividers) != 1:
        raise ValueError(f"expected one divider, got {dividers}")
    divider = dividers[0]
    top = [list(row) for row in grid[:divider]]
    bottom = [list(row) for row in grid[divider + 1 :]]
    if len(top) != len(bottom):
        raise ValueError("unequal panel heights")
    return top, bottom


def boolean_output(
    grid: list[list[int]], predicate: Callable[[bool, bool], bool]
) -> list[list[int]]:
    top, bottom = split_panels(grid)
    return [
        [8 if predicate(top[r][c] != 0, bottom[r][c] != 0) else 0
         for c in range(len(top[0]))]
        for r in range(len(top))
    ]


def intersection_output(grid: list[list[int]]) -> list[list[int]]:
    return boolean_output(grid, lambda top, bottom: top and bottom)


def union_output(grid: list[list[int]]) -> list[list[int]]:
    return boolean_output(grid, lambda top, bottom: top or bottom)


def xor_output(grid: list[list[int]]) -> list[list[int]]:
    return boolean_output(grid, lambda top, bottom: top != bottom)


def occupancy_counts(grid: list[list[int]]) -> dict[str, int]:
    top, bottom = split_panels(grid)
    counts = {"00": 0, "10": 0, "01": 0, "11": 0}
    for r in range(len(top)):
        for c in range(len(top[0])):
            key = f"{int(top[r][c] != 0)}{int(bottom[r][c] != 0)}"
            counts[key] += 1
    return counts


def panel_colors(grid: list[list[int]]) -> tuple[int, int]:
    top, bottom = split_panels(grid)
    top_colors = {value for row in top for value in row if value != 0}
    bottom_colors = {value for row in bottom for value in row if value != 0}
    if len(top_colors) != 1 or len(bottom_colors) != 1:
        raise ValueError((top_colors, bottom_colors))
    return next(iter(top_colors)), next(iter(bottom_colors))
