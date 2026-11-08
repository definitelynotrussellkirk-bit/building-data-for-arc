"""Visible-example solution for reviewer solve episode ebff81ea3252."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    result = deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if grid else 0
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            cells = (
                (row, col),
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            )
            if all(grid[r][c] == 3 for r, c in cells):
                for r, c in cells:
                    result[r][c] = 7
    return result
