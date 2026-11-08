"""Visible-example solution for f4725b891d89."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    if len(grid) < 3 or not grid or len(grid[0]) < 3:
        return out

    height, width = len(grid), len(grid[0])
    top = [
        (column, grid[1][column])
        for column in range(2, width - 1)
        if grid[1][column] not in (0, 5)
    ]
    left = [
        (row, grid[row][1])
        for row in range(2, height - 1)
        if grid[row][1] not in (0, 5)
    ]

    for row, row_color in left:
        for column, column_color in top:
            if row_color == column_color:
                out[row][column] = row_color
    return out
