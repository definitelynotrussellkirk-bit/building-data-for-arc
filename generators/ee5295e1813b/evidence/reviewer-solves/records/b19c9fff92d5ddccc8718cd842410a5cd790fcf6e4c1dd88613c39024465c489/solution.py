"""Visible-example solution for ee5295e1813b."""
from __future__ import annotations


def solve(grid):
    """Fill blank centers surrounded diagonally by one shared nonzero color."""
    if not grid:
        return []
    out = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            diagonals = (
                grid[row - 1][col - 1],
                grid[row - 1][col + 1],
                grid[row + 1][col - 1],
                grid[row + 1][col + 1],
            )
            color = diagonals[0]
            if color != 0 and all(value == color for value in diagonals[1:]):
                out[row][col] = color
    return out
