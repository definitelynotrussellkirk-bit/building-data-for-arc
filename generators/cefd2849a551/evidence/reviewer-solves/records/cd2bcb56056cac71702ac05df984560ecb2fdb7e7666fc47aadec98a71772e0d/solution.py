"""Visible-example solution for cefd2849a551."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep exactly the orthogonal boundary of each nonzero colored object."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            if any(
                not (0 <= row + dr < height and 0 <= col + dc < width)
                or grid[row + dr][col + dc] != color
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                result[row][col] = color
    return result
