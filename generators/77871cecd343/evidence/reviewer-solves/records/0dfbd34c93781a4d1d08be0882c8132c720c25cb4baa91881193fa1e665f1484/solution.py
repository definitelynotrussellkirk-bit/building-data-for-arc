from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Reflect the color-1 object through the visible color-9 cross.

    The original object stays color 1. Every distinct reflected copy is color 8;
    the color-9 row and column remain unchanged.
    """
    height = len(grid)
    width = len(grid[0])

    cross_rows = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    cross_cols = [
        c
        for c in range(width)
        if all(grid[r][c] == 9 for r in range(height))
    ]
    if len(cross_rows) != 1 or len(cross_cols) != 1:
        raise ValueError("expected exactly one full color-9 row and column")

    axis_row = cross_rows[0]
    axis_col = cross_cols[0]
    source = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]

    out = [row[:] for row in grid]
    for r, c in source:
        reflected = {
            (r, 2 * axis_col - c),
            (2 * axis_row - r, c),
            (2 * axis_row - r, 2 * axis_col - c),
        }
        for rr, cc in reflected:
            if not (0 <= rr < height and 0 <= cc < width):
                raise ValueError("reflected copy leaves the grid")
            if out[rr][cc] == 0:
                out[rr][cc] = 8

    return out
