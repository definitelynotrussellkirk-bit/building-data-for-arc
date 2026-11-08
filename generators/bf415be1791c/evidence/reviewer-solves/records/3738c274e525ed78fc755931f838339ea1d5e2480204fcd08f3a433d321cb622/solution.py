"""Visible-example solution for bf415be1791c."""
from __future__ import annotations


def solve(grid):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    height = len(grid)
    divider_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(divider_columns) != 1:
        raise ValueError("expected exactly one full-height gray divider")
    divider = divider_columns[0]

    output = [row[:] for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 6:
                continue
            mirror_col = 2 * divider - col
            if 0 <= mirror_col < width and output[row][mirror_col] == 0:
                output[row][mirror_col] = 8
    return output
