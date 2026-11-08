"""Independent review helpers for task 8921bea21bbb.

The helper intentionally does not import semantic functions from generator.py.
It gives task tests and future reviewers a source-independent parser, rule
mirror, and generator loader.
"""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
from typing import Any

TASK_HOME = Path(__file__).resolve().parents[1]
TASK_ID = "8921bea21bbb"


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_HOME / "generator.py")
    spec = importlib.util.spec_from_file_location("review_8921bea21bbb_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_grid(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
        and all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    )


def split_panels(grid: list[list[int]]) -> tuple[int, list[list[int]], list[list[int]]]:
    if not valid_grid(grid):
        raise ValueError("expected a nonempty rectangular ARC grid")
    height = len(grid)
    width = len(grid[0])
    separators = [
        column
        for column in range(width)
        if all(grid[row][column] == 9 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError(f"expected exactly one full-height 9 separator, got {separators}")
    separator = separators[0]
    if separator * 2 + 1 != width:
        raise ValueError(f"separator at {separator} does not split width {width} equally")
    left = [list(row[:separator]) for row in grid]
    right = [list(row[separator + 1 :]) for row in grid]
    return separator, left, right


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    """Mirror the canonical rule independently of the reviewed generator."""
    _, left, right = split_panels(grid)
    return [
        [right[row][column] if left[row][column] != 0 else 0 for column in range(len(left[0]))]
        for row in range(len(left))
    ]


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    separator, left, right = split_panels(grid)
    left_nonzero = [
        (row, column, value)
        for row, values in enumerate(left)
        for column, value in enumerate(values)
        if value != 0
    ]
    right_nonzero = [
        (row, column, value)
        for row, values in enumerate(right)
        for column, value in enumerate(values)
        if value != 0
    ]
    mask_colors = {value for _, _, value in left_nonzero}
    overlap_colors = {
        right[row][column]
        for row, column, _ in left_nonzero
        if right[row][column] != 0
    }
    return {
        "panel_h": len(grid),
        "panel_w": separator,
        "mask_count": len(left_nonzero),
        "mask_color": next(iter(mask_colors)) if len(mask_colors) == 1 else None,
        "right_zero_count": sum(value == 0 for row in right for value in row),
        "mask_colors": mask_colors,
        "right_colors": {value for _, _, value in right_nonzero},
        "overlap_colors": overlap_colors,
        "right_only_count": sum(
            left[row][column] == 0 and right[row][column] != 0
            for row in range(len(left))
            for column in range(len(left[0]))
        ),
        "output": independent_rule(copy.deepcopy(grid)),
    }


def color2_only_rival(grid: list[list[int]]) -> list[list[int]]:
    _, left, right = split_panels(grid)
    return [
        [right[row][column] if left[row][column] == 2 else 0 for column in range(len(left[0]))]
        for row in range(len(left))
    ]
