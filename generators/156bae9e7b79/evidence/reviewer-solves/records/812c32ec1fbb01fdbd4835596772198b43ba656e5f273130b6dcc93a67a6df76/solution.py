"""Visible-example solution for ARC task 156bae9e7b79."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])

    # The structural cyan line is the single column containing 8 below row 0.
    candidates = [
        col
        for col in range(width)
        if any(grid[row][col] == 8 for row in range(1, height))
    ]
    if len(candidates) != 1:
        raise ValueError(f"expected one cyan line column, got {candidates}")
    line_col = candidates[0]
    line_rows = [row for row in range(1, height) if grid[row][line_col] == 8]
    line_top, line_bottom = min(line_rows), max(line_rows)

    key = grid[0]
    output = [[5 for _ in range(width)] for _ in range(height)]
    max_radius = (width - 1) // 2
    for row in range(line_top, line_bottom + 1):
        radius = min(max_radius, row - line_top)
        for col in range(width):
            if col == line_col:
                output[row][col] = 8
            elif line_col - radius <= col <= line_col + radius:
                output[row][col] = key[col]
    return output
