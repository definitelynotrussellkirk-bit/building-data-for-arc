"""Visible-example-only solution for blind task 8b6543be4517."""


def solve(grid):
    """Mirror every 7 across the solid 8 separator, keeping in-bounds mirrors."""
    out = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0

    separator_rows = [r for r, row in enumerate(grid) if row and all(v == 8 for v in row)]
    separator_cols = [
        c for c in range(w)
        if h and all(grid[r][c] == 8 for r in range(h))
    ]

    if len(separator_rows) + len(separator_cols) != 1:
        raise ValueError("expected exactly one solid separator row or column")

    sevens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7]
    if separator_rows:
        axis = separator_rows[0]
        for r, c in sevens:
            rr = 2 * axis - r
            if 0 <= rr < h:
                out[rr][c] = 7
    else:
        axis = separator_cols[0]
        for r, c in sevens:
            cc = 2 * axis - c
            if 0 <= cc < w:
                out[r][cc] = 7

    return out
