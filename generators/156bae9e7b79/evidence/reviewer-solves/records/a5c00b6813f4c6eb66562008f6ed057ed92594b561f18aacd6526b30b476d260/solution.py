"""Visible-example solution for the reviewer-authored keyed projection episode."""
from __future__ import annotations


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    key = list(grid[0])

    cyan = [
        (row, col)
        for row in range(1, height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    line_col = cyan[0][1]
    line_rows = [row for row, col in cyan if col == line_col]
    line_top = min(line_rows)
    line_bottom = max(line_rows)

    result = [[5 for _ in range(width)] for _ in range(height)]
    max_radius = (width - 1) // 2
    for row in range(line_top, line_bottom + 1):
        radius = min(max_radius, row - line_top)
        for col in range(max(0, line_col - radius), min(width, line_col + radius + 1)):
            result[row][col] = 8 if col == line_col else key[col]
    return result
