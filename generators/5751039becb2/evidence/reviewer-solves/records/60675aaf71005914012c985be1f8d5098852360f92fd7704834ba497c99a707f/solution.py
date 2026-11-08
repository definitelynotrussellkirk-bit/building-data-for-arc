from __future__ import annotations

from typing import Sequence

Grid = list[list[int]]


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Keep nonzero cells having an equal-colored diagonal neighbor."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output: Grid = [[0 for _ in range(width)] for _ in range(height)]

    diagonal_offsets = ((-1, -1), (-1, 1), (1, -1), (1, 1))
    for row in range(height):
        if len(grid[row]) != width:
            raise ValueError("grid must be rectangular")
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            if any(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == color
                for dr, dc in diagonal_offsets
            ):
                output[row][col] = color
    return output
