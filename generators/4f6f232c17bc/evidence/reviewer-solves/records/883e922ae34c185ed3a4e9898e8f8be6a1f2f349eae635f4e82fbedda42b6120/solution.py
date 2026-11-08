"""Visible-example solution for ARC task 4f6f232c17bc."""

from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Reflect blue cells across the full-height gray divider, recoloring cyan.

    All non-result cells are cleared. Reflections outside the input bounds are
    clipped one cell at a time.
    """
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    divider_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(divider_columns) != 1:
        raise ValueError("expected exactly one full-height gray divider")
    axis = divider_columns[0]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1:
                continue
            reflected_col = 2 * axis - col
            if 0 <= reflected_col < width:
                output[row][reflected_col] = 8
    return output
