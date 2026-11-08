"""Visible-example solution for task 8d2cfdfec79c."""
from __future__ import annotations


def solve(grid):
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])

    # Normal dicts preserve insertion order. Scanning row-major therefore
    # records the examples' apparent rectangle-overwrite order.
    cells_by_color = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                cells_by_color.setdefault(color, []).append((row_index, column_index))

    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in cells_by_color.items():
        if len(cells) < 2:
            continue
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(column for _, column in cells)
        right = max(column for _, column in cells)
        for row in range(top, bottom + 1):
            output[row][left] = color
            output[row][right] = color
        for column in range(left, right + 1):
            output[top][column] = color
            output[bottom][column] = color
    return output
