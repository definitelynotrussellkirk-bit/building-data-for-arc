"""Visible-example solution for task 2038a3a66886."""
from __future__ import annotations


def solve(grid):
    out = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        # Process each non-background color independently, in first-seen order.
        for color in dict.fromkeys(value for value in row if value != 0):
            columns = [col for col, value in enumerate(row) if value == color]
            if len(columns) >= 2:
                for col in range(columns[0], columns[-1] + 1):
                    out[row_index][col] = color
    return out
