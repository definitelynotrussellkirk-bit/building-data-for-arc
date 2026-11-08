"""Visible-example solution for the prepared ARC task."""
from __future__ import annotations


def solve(grid):
    out = [list(row) for row in grid]
    colors = sorted({value for row in grid for value in row if value != 0})

    for color in colors:
        cells = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        if len(cells) != 3:
            continue
        rows = sorted({row for row, _ in cells})
        cols = sorted({col for _, col in cells})
        if len(rows) != 2 or len(cols) != 2:
            continue

        corners = {(row, col) for row in rows for col in cols}
        missing = corners - set(cells)
        if len(missing) != 1:
            continue
        row, col = next(iter(missing))
        if grid[row][col] == 0:
            out[row][col] = color

    return out
