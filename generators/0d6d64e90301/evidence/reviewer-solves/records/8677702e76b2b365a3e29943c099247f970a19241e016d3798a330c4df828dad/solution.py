"""Visible-example solution for task 0d6d64e90301."""

from __future__ import annotations

from typing import Sequence

Grid = list[list[int]]


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Replace each input cell by a 2-by-2 block of the same color."""
    if not grid:
        return []
    width = len(grid[0])
    if width == 0:
        return [[] for _ in range(0)]
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    output: Grid = []
    for row in grid:
        expanded_row = [value for value in row for _ in range(2)]
        output.append(expanded_row.copy())
        output.append(expanded_row.copy())
    return output
