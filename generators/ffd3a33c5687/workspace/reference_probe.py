"""Independent probes for the ffd3a33c5687 left-priority mirror rule.

This file deliberately does not import the generator.  Future reviewers can use
it to compare the Python mirror, the canonical examples, and executable rival
rules without accidentally making the generator its own oracle.
"""
from __future__ import annotations

import copy
from typing import Any

Grid = list[list[int]]


def shape_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list"
    if not all(isinstance(row, list) for row in grid):
        return "every row must be a list"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid values must be integer ARC colors 0..9"
    return None


def _checked(grid: Any) -> Grid:
    error = shape_error(grid)
    if error:
        raise ValueError(error)
    return grid


def left_priority_output(grid: Grid) -> Grid:
    """Authoritative behavior: nonzero left member wins each mirror orbit."""
    source = _checked(grid)
    output = copy.deepcopy(source)
    width = len(source[0])
    for row_index, row in enumerate(source):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            color = row[left_col] if row[left_col] != 0 else row[right_col]
            output[row_index][left_col] = color
            output[row_index][right_col] = color
    return output


def preserve_conflicts_output(grid: Grid) -> Grid:
    """Canonical-fitting rival: fill a blank mate, but preserve occupied conflicts."""
    source = _checked(grid)
    output = copy.deepcopy(source)
    width = len(source[0])
    for row_index, row in enumerate(source):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            if left == 0 and right != 0:
                output[row_index][left_col] = right
            elif right == 0 and left != 0:
                output[row_index][right_col] = left
    return output


def right_priority_output(grid: Grid) -> Grid:
    """Canonical-fitting rival: nonzero right member wins each mirror orbit."""
    source = _checked(grid)
    output = copy.deepcopy(source)
    width = len(source[0])
    for row_index, row in enumerate(source):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            color = row[right_col] if row[right_col] != 0 else row[left_col]
            output[row_index][left_col] = color
            output[row_index][right_col] = color
    return output


def orbit_counts(grid: Grid) -> dict[str, int]:
    source = _checked(grid)
    width = len(source[0])
    counts = {"n_singletons": 0, "n_pairs": 0, "n_conflicts": 0}
    for row in source:
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            if (left == 0) != (right == 0):
                counts["n_singletons"] += 1
            elif left != 0 and left == right:
                counts["n_pairs"] += 1
            elif left != 0 and right != 0 and left != right:
                counts["n_conflicts"] += 1
    return counts


def profile(grid: Grid) -> tuple[int, int, int]:
    source = _checked(grid)
    return len(source), len(source[0]), len({value for row in source for value in row})


def exact_counterexample() -> Grid:
    """Small legal witness: left=2/right=3 forces a left-priority decision."""
    return [
        [0, 0, 0, 0, 0],
        [0, 2, 0, 3, 0],
        [4, 0, 0, 0, 0],
        [0, 0, 0, 0, 5],
        [0, 0, 0, 0, 0],
    ]
