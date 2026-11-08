"""Visible-example solution for task ad92d10d919c."""
from __future__ import annotations


def solve(grid):
    """Fill a zero center exactly when its four diagonal neighbors agree."""
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
