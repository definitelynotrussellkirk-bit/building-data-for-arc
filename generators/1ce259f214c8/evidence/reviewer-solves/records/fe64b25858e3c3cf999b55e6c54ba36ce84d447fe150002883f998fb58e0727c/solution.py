"""Visible-example solution for the prepared 1ce259f214c8 episode."""
from __future__ import annotations

from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """XOR the occupancy masks on the two sides of the gray divider."""
    if not grid or not grid[0]:
        raise ValueError("grid must be nonempty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_columns = [
        column
        for column in range(width)
        if all(row[column] == 5 for row in grid)
    ]
    if len(divider_columns) != 1:
        raise ValueError("expected one full-height gray divider")
    divider = divider_columns[0]
    right_width = width - divider - 1
    if divider != right_width:
        raise ValueError("divider must split equal-width panels")

    return [
        [
            8 if ((row[column] != 0) != (row[divider + 1 + column] != 0)) else 0
            for column in range(divider)
        ]
        for row in grid
    ]
