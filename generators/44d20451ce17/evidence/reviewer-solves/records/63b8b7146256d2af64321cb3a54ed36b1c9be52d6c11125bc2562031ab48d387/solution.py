from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Move every column's blue marker(s) to one blue cell on the bottom row.

    All non-blue cells are preserved. Multiple blue cells in the same column
    collapse to a single blue destination because the examples mark columns,
    not individual falling objects.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    out = [row[:] for row in grid]
    marked_columns = {
        col
        for row in grid
        for col, value in enumerate(row)
        if value == 1
    }

    for row_index, row in enumerate(out):
        for col, value in enumerate(row):
            if value == 1:
                out[row_index][col] = 0

    for col in marked_columns:
        out[-1][col] = 1

    return out
