"""Visible-example solution for the exposed post-repair episode."""
from __future__ import annotations


def solve(grid):
    """Complete every monochrome 2x2 window with one missing corner."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])

    for row in range(height - 1):
        for col in range(width - 1):
            cells = (
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            )
            values = [source[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1 and values.count(0) == 1:
                missing = values.index(0)
                target_row, target_col = cells[missing]
                output[target_row][target_col] = nonzero[0]

    return output
