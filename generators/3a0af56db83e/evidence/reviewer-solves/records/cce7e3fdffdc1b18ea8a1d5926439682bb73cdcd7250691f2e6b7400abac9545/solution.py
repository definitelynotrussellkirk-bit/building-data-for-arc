"""Visible-example solution for the four stacked-mask overlay task."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if len(grid) != 12 or not grid or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a rectangular 12-row grid")
    width = len(grid[0])
    output = [[0] * width for _ in range(3)]
    for row in range(3):
        for col in range(width):
            for band in (0, 1, 3, 2):
                value = grid[band * 3 + row][col]
                if value != 0:
                    output[row][col] = value
                    break
    return output
