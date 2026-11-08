"""Visible-example solution for Connect Aligned Pairs."""
from __future__ import annotations

from collections import defaultdict


def solve(grid):
    """Connect each same-color aligned marker pair, inclusive, on a zero grid."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    positions = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (row0, column0), (row1, column1) = cells
        if row0 == row1:
            for column in range(min(column0, column1), max(column0, column1) + 1):
                output[row0][column] = color
        elif column0 == column1:
            for row in range(min(row0, row1), max(row0, row1) + 1):
                output[row][column0] = color
    return output
