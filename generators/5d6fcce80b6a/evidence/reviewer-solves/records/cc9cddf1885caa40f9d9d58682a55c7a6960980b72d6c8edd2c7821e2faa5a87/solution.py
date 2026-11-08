from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Tile the input on the main diagonal and mark non-trailing blank rows."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    out = [[0 for _ in range(2 * width)] for _ in range(2 * height)]

    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            out[row_index][column_index] = value
            out[row_index + height][column_index + width] = value

    occupied_rows = [index for index, row in enumerate(grid) if any(value != 0 for value in row)]
    last_occupied_row = max(occupied_rows, default=-1)
    for row_index, row in enumerate(grid):
        if row_index < last_occupied_row and all(value == 0 for value in row):
            out[row_index] = [3] * (2 * width)
            out[row_index + height] = [3] * (2 * width)

    return out
