"""Visible-example solution for the post-repair beam task."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    """Extend each nonzero top-row color downward until a 9 blocker."""
    output = deepcopy(grid)
    if not grid:
        return output
    height = len(grid)
    width = len(grid[0])
    for column in range(width):
        color = grid[0][column]
        if color in (0, 9):
            continue
        for row in range(1, height):
            if grid[row][column] == 9:
                break
            output[row][column] = color
    return output
