"""Visible-example solution for the post-repair ARC episode."""
from __future__ import annotations


def solve(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if width == 0 or width % 2:
        raise ValueError("expected an even, nonzero column count")
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    return [
        [value for start in range(width - 2, -1, -2) for value in row[start:start + 2]]
        for row in grid
    ]
