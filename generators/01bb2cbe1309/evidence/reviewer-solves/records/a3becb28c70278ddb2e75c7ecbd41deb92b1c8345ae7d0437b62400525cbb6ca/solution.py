"""Visible-example solution for the prepared 01bb2cbe1309 challenge."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete clean equal-color diagonals into their enclosing 2x2 block."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    output = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    for row in range(height - 1):
        for col in range(width - 1):
            top_left = grid[row][col]
            top_right = grid[row][col + 1]
            bottom_left = grid[row + 1][col]
            bottom_right = grid[row + 1][col + 1]

            if (
                top_left != 0
                and top_left == bottom_right
                and top_right == 0
                and bottom_left == 0
            ):
                output[row][col + 1] = top_left
                output[row + 1][col] = top_left
            elif (
                top_right != 0
                and top_right == bottom_left
                and top_left == 0
                and bottom_right == 0
            ):
                output[row][col] = top_right
                output[row + 1][col + 1] = top_right

    return output
