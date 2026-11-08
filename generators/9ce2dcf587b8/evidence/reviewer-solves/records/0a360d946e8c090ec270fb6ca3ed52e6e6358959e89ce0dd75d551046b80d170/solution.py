"""Visible-example solution for task 9ce2dcf587b8."""


def solve(grid):
    """Extend every nonzero source cell along both full diagonals."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    sources = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    for row, col, value in sources:
        for delta_row, delta_col in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            rr, cc = row, col
            while 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = value
                rr += delta_row
                cc += delta_col
    return out
