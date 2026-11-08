"""Visible-example solution for ARC task 70205357c60a."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5:
                continue
            if (
                row > 0
                and row + 1 < height
                and col > 0
                and col + 1 < width
                and grid[row - 1][col] == 5
                and grid[row + 1][col] == 5
                and grid[row][col - 1] == 5
                and grid[row][col + 1] == 5
            ):
                output[row][col] = 2
    return output
