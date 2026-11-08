"""Visible-example solution for task 2dae2c34641b."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]

    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        if len(cells) != 2:
            raise ValueError(f"color {color} has {len(cells)} endpoints, expected 2")
        (upper_row, upper_col), (lower_row, lower_col) = sorted(cells)
        for row in range(upper_row, lower_row + 1):
            out[row][upper_col] = color
        step = 1 if lower_col >= upper_col else -1
        for col in range(upper_col, lower_col + step, step):
            out[lower_row][col] = color
    return out
