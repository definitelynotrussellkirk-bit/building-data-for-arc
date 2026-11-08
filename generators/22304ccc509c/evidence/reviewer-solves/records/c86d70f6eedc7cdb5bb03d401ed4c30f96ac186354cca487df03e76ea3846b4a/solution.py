"""Visible-example solution for 22304ccc509c."""
from __future__ import annotations


def solve(grid):
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for column in range(width):
        values = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        first = height - len(values)
        for offset, value in enumerate(values):
            out[first + offset][column] = value
    return out
