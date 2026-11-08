"""Visible-example solution for reviewer solve episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Split the 8-column input into aligned 4-column halves.

    Emit 4 at an output position exactly when both aligned input cells are 0;
    emit 0 otherwise.
    """
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    if any(not isinstance(row, list) or len(row) != 8 for row in grid):
        raise ValueError("each input row must contain exactly 8 cells")
    return [
        [4 if row[col] == 0 and row[col + 4] == 0 else 0 for col in range(4)]
        for row in grid
    ]
