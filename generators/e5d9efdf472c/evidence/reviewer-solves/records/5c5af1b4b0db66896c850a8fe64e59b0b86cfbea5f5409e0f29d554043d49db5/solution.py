"""Visible-example solution for the blind ARC episode."""


def solve(grid):
    """Connect the two magenta (6) cells with azure (8) cells."""
    out = [row[:] for row in grid]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    if len(markers) != 2:
        return out

    (r1, c1), (r2, c2) = markers
    if r1 == r2:
        for c in range(min(c1, c2) + 1, max(c1, c2)):
            if out[r1][c] == 0:
                out[r1][c] = 8
    elif c1 == c2:
        for r in range(min(r1, r2) + 1, max(r1, r2)):
            if out[r][c1] == 0:
                out[r][c1] = 8
    return out
