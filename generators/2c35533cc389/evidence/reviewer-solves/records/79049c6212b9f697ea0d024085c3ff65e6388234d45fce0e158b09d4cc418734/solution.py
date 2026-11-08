"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid):
    """Preserve the grid and paint blue immediately right of each input red."""
    output = [list(row) for row in grid]
    width = len(grid[0])
    sources = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    for row, col in sources:
        if col + 1 < width:
            output[row][col + 1] = 1
    return output
