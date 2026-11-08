"""Visible-example solution for the post-repair reviewer solve."""
from __future__ import annotations


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be a nonempty rectangle")

    height, width = len(grid), len(grid[0])
    full_rows = [r for r in range(height) if all(grid[r][c] == 5 for c in range(width))]
    full_cols = [c for c in range(width) if all(grid[r][c] == 5 for r in range(height))]
    if len(full_rows) + len(full_cols) != 1:
        raise ValueError("expected exactly one complete color-5 divider")

    output = [list(row) for row in grid]
    if full_cols:
        divider = full_cols[0]
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 2:
                    reflected_c = 2 * divider - c
                    if 0 <= reflected_c < width and output[r][reflected_c] == 0:
                        output[r][reflected_c] = 3
    else:
        divider = full_rows[0]
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 2:
                    reflected_r = 2 * divider - r
                    if 0 <= reflected_r < height and output[reflected_r][c] == 0:
                        output[reflected_r][c] = 3
    return output
