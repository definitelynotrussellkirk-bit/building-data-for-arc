"""Visible-example solution for reviewer solve task 5d321adb3a28."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill a zero bracketed by the same nonzero color left/right or up/down."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]

    for row in range(height):
        for column in range(width):
            if grid[row][column] != 0:
                continue

            if 0 < column < width - 1:
                color = grid[row][column - 1]
                if color != 0 and color == grid[row][column + 1]:
                    output[row][column] = color
                    continue

            if 0 < row < height - 1:
                color = grid[row - 1][column]
                if color != 0 and color == grid[row + 1][column]:
                    output[row][column] = color

    return output
