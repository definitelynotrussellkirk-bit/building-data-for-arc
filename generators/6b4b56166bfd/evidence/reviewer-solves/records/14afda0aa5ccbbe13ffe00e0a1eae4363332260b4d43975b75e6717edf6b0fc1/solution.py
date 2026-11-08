"""Visible-example solution for the reviewer solve episode."""


def solve(grid):
    """Copy each colored seed through its four quarter-turn orbit around 5."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]

    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if len(pivots) != 1:
        raise ValueError("expected exactly one color-5 pivot")
    pr, pc = pivots[0]

    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    for r, c, value in seeds:
        dr, dc = r - pr, c - pc
        for rr, cc in ((dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)):
            nr, nc = pr + rr, pc + cc
            if 0 <= nr < height and 0 <= nc < width:
                output[nr][nc] = value

    return output
