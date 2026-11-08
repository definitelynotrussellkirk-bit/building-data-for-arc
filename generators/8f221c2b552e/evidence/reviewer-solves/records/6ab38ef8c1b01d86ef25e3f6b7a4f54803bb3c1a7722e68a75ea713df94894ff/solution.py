"""Visible-example solution for task 8f221c2b552e."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    """Fill each same-color pair horizontally within its own row."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        positions_by_color = {}
        for column, color in enumerate(row):
            if color != 0:
                positions_by_color.setdefault(color, []).append(column)
        for color, columns in positions_by_color.items():
            if len(columns) >= 2:
                for column in range(min(columns), max(columns) + 1):
                    output[row_index][column] = color
    return output
