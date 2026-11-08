"""Visible-example solution: crop to the tight box containing every nonzero cell."""
from __future__ import annotations


def solve(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return [[0]]
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    return [list(values[col0 : col1 + 1]) for values in grid[row0 : row1 + 1]]
