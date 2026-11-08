"""Visible-example solution for task 113d9bb402d3."""
from __future__ import annotations


def solve(grid):
    """Recolour blue cells inside the cyan marker bounding box green."""
    cyan = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    ]
    if not cyan:
        return [list(row) for row in grid]

    top = min(row for row, _ in cyan)
    bottom = max(row for row, _ in cyan)
    left = min(col for _, col in cyan)
    right = max(col for _, col in cyan)

    output = [list(row) for row in grid]
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if output[row][col] == 1:
                output[row][col] = 3
    return output
