"""Visible-example solution for reviewer solve episode 302ddfbe2baa."""
from __future__ import annotations


def solve(grid):
    """Paint 8s rightward from each 4, stopping before the first 9."""
    out = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height):
        for source_col, value in enumerate(grid[row]):
            if value != 4:
                continue
            for col in range(source_col + 1, width):
                if grid[row][col] == 9:
                    break
                if grid[row][col] == 0:
                    out[row][col] = 8
    return out
