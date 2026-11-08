"""Visible-example solution for blind task 8a63cd5c5bfb."""


def solve(grid):
    """Outline the rectangle whose opposite corners are the two color-3 cells.

    Existing nonzero cells are preserved. Empty perimeter cells become color 8.
    """
    out = [row[:] for row in grid]
    corners = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    if len(corners) != 2:
        return out

    (r1, c1), (r2, c2) = corners
    top, bottom = sorted((r1, r2))
    left, right = sorted((c1, c2))

    perimeter = (
        [(top, c) for c in range(left, right + 1)]
        + [(bottom, c) for c in range(left, right + 1)]
        + [(r, left) for r in range(top + 1, bottom)]
        + [(r, right) for r in range(top + 1, bottom)]
    )
    for r, c in perimeter:
        if out[r][c] == 0:
            out[r][c] = 8
    return out
