"""Visible-example solution for task 144582f287b5."""
from __future__ import annotations


def solve(grid):
    """Move the fixed 2x2 block at rows/cols 1..2 to the four corners."""
    if not isinstance(grid, list) or len(grid) < 4:
        raise ValueError("expected at least four rows")
    if not grid or not isinstance(grid[0], list) or len(grid[0]) < 4:
        raise ValueError("expected at least four columns")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    height = len(grid)
    output = [[0 for _ in range(width)] for _ in range(height)]
    output[0][0] = grid[1][1]
    output[0][width - 1] = grid[1][2]
    output[height - 1][0] = grid[2][1]
    output[height - 1][width - 1] = grid[2][2]
    return output
