"""Visible-example solution for the prepared ARC episode."""
from __future__ import annotations


def solve(grid):
    """Fill each occupied column's inclusive vertical extent with color 8."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return []
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    height = len(grid)
    output = [[0 for _ in range(width)] for _ in range(height)]
    for column in range(width):
        occupied_rows = [row for row in range(height) if grid[row][column] != 0]
        if not occupied_rows:
            continue
        for row in range(min(occupied_rows), max(occupied_rows) + 1):
            output[row][column] = 8
    return output
