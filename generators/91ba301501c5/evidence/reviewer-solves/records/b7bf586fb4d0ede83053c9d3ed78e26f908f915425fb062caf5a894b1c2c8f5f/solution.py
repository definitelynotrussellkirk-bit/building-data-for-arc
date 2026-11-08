def solve(grid):
    """Extend colored markers vertically relative to the horizontal gray divider."""
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0])

    divider = next(
        r for r, row in enumerate(out)
        if len(row) == width and all(value == 5 for value in row)
    )

    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        if r != divider
        for c, value in enumerate(row)
        if value in (1, 2)
    ]

    for r, c, value in markers:
        if r < divider:
            rows = range(0, r + 1) if value == 1 else range(r, divider)
        else:
            rows = range(r, height) if value == 1 else range(divider + 1, r + 1)
        for rr in rows:
            if out[rr][c] == 0:
                out[rr][c] = value

    return out
