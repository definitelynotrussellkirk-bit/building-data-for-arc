def solve(grid):
    """Copy the color-1 stencil from its color-2 anchor to the color-3 anchor in color 8."""
    out = [row[:] for row in grid]
    ones = []
    anchor2 = None
    anchor3 = None

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 1:
                ones.append((r, c))
            elif value == 2:
                anchor2 = (r, c)
            elif value == 3:
                anchor3 = (r, c)

    if anchor2 is None or anchor3 is None:
        return out

    r2, c2 = anchor2
    r3, c3 = anchor3
    height = len(grid)
    width = len(grid[0]) if height else 0

    for r, c in ones:
        rr = r3 + (r - r2)
        cc = c3 + (c - c2)
        if 0 <= rr < height and 0 <= cc < width:
            out[rr][cc] = 8

    return out
