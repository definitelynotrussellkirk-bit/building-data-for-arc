"""Visible-example solution for 78f3cf31c4bf."""
from __future__ import annotations


def solve(grid):
    """Fill the missing corner of each same-colour 3-of-4 2x2 window once."""
    output = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height - 1):
        for col in range(width - 1):
            cells = (
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            )
            values = [grid[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1 and values.count(0) == 1:
                missing = cells[values.index(0)]
                output[missing[0]][missing[1]] = nonzero[0]
    return output
