"""Visible-example solution for the final 00b92ce63593 review episode."""
from __future__ import annotations


def solve(grid):
    if not grid:
        return []
    header = list(grid[0])
    output = [[0 for _ in row] for row in grid]
    for row_index in range(1, len(grid)):
        for col_index, value in enumerate(grid[row_index]):
            if value != 0:
                output[row_index][col_index] = header[col_index]
    return output
