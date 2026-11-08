"""Visible-example solution for task 8dbffe99308f."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Overlay nonzero cells with their reflection across the anti-diagonal."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty square list")
    size = len(grid)
    if any(not isinstance(row, list) or len(row) != size for row in grid):
        raise ValueError("grid must be square")

    source = [row[:] for row in grid]
    output = [row[:] for row in grid]
    for row_index, row in enumerate(source):
        for column_index, color in enumerate(row):
            if color != 0:
                mirror_row = size - 1 - column_index
                mirror_column = size - 1 - row_index
                output[mirror_row][mirror_column] = color
    return output
