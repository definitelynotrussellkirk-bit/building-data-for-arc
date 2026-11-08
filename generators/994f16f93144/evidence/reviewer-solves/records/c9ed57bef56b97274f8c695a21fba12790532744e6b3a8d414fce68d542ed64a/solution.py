"""Visible-example solution for ARC task 994f16f93144."""
from __future__ import annotations


def solve(grid):
    """Recolor centers of same-color length-3 diagonal windows to cyan (8)."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            color = grid[row][col]
            if color == 0:
                continue
            if (
                grid[row - 1][col - 1] == color == grid[row + 1][col + 1]
                or grid[row - 1][col + 1] == color == grid[row + 1][col - 1]
            ):
                out[row][col] = 8
    return out
