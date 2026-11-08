"""Visible-example solution for review task 74a14031dc79."""
from __future__ import annotations


def solve(grid):
    """Overlay the two 3-column panels by nonzero occupancy using blue (2)."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    if any(not isinstance(row, list) or len(row) != 7 for row in grid):
        raise ValueError("each row must contain two 3-column panels and one separator")
    return [
        [2 if row[column] != 0 or row[column + 4] != 0 else 0 for column in range(3)]
        for row in grid
    ]
