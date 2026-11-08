"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    background = grid[0][0]
    dot_row = dot_col = None
    for row in range(height):
        for col in range(width):
            if grid[row][col] != background:
                dot_row, dot_col = row, col
                break
        if dot_row is not None:
            break
    if dot_row is None:
        raise ValueError("expected one non-background dot")

    out = [list(row) for row in grid]
    for row in range(height):
        if row != dot_row:
            out[row][dot_col] = 1

    if dot_row == dot_col:
        top_corner_col = width - 1
        bottom_corner_col = 0
    else:
        top_corner_col = 0
        bottom_corner_col = width - 1

    for col in range(min(dot_col, top_corner_col), max(dot_col, top_corner_col) + 1):
        if out[0][col] == background:
            out[0][col] = 1
    for col in range(min(dot_col, bottom_corner_col), max(dot_col, bottom_corner_col) + 1):
        if out[height - 1][col] == background:
            out[height - 1][col] = 1
    return out
