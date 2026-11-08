"""Row-local color-span completion inferred from the visible demonstrations."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError('grid must have at least one row')
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        raise ValueError('grid rows must be nonempty sequences')
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError('grid must be rectangular')
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        raise ValueError('grid cells must be integer colors 0..9')

    result = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        positions: dict[int, list[int]] = {}
        for col, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append(col)
        for color, columns in positions.items():
            if len(columns) >= 2:
                first, last = columns[0], columns[-1]
                result[row_index][first:last + 1] = [color] * (last - first + 1)
    return result
