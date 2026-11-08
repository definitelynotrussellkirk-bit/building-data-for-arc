def solve(grid):
    """Connect the two color-6 cells in their shared row/column with color 8."""
    out = [row[:] for row in grid]
    sixes = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    if len(sixes) != 2:
        return out

    (r1, c1), (r2, c2) = sixes
    if r1 == r2:
        for c in range(min(c1, c2) + 1, max(c1, c2)):
            out[r1][c] = 8
    elif c1 == c2:
        for r in range(min(r1, r2) + 1, max(r1, r2)):
            out[r][c1] = 8
    return out
