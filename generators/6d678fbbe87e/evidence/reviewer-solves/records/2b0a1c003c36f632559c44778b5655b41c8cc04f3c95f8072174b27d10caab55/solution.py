"""Visible-example solution for 6d678fbbe87e."""
from __future__ import annotations


def solve(grid):
    """Complete every qualifying 2x2 window in one simultaneous pass."""
    output = [list(row) for row in grid]
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
                missing = values.index(0)
                target_row, target_col = cells[missing]
                output[target_row][target_col] = nonzero[0]
    return output
