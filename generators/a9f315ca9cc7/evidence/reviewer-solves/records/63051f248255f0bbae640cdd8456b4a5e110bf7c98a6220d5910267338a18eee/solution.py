"""Visible-example solution for a9f315ca9cc7."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Use the input as both a block mask and the block template.

    Each nonzero input cell selects a full copy of the input in the matching
    output block; each zero input cell selects an all-zero block.
    """
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width * width)] for _ in range(height * height)]
    for block_row in range(height):
        for block_col in range(width):
            if grid[block_row][block_col] == 0:
                continue
            for row in range(height):
                for col in range(width):
                    output[block_row * height + row][block_col * width + col] = grid[row][col]
    return output
