"""Visible-example solution for blind ARC task 77871cecd343."""


def solve(grid):
    """Reflect the colored motif into the other three divider quadrants.

    A complete row and column of 9s form the horizontal and vertical mirrors.
    Existing motif cells (color 1) stay unchanged; each valid reflection across
    either or both mirror lines is drawn with color 8.
    """
    out = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    divider_rows = [
        r for r, row in enumerate(grid)
        if row and all(value == 9 for value in row)
    ]
    divider_cols = [
        c for c in range(width)
        if all(grid[r][c] == 9 for r in range(height))
    ]
    if len(divider_rows) != 1 or len(divider_cols) != 1:
        raise ValueError("expected exactly one full divider row and column")

    mirror_r = divider_rows[0]
    mirror_c = divider_cols[0]
    motif = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]

    for r, c in motif:
        for rr, cc in (
            (2 * mirror_r - r, c),
            (r, 2 * mirror_c - c),
            (2 * mirror_r - r, 2 * mirror_c - c),
        ):
            if 0 <= rr < height and 0 <= cc < width and out[rr][cc] == 0:
                out[rr][cc] = 8

    return out
