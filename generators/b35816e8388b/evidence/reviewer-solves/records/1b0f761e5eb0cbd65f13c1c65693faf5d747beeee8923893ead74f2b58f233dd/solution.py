"""Visible-example-only solution for blind task b35816e8388b."""


def solve(grid):
    """Replace the two yellow markers with one azure marker at their midpoint."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    ]
    if len(points) != 2:
        raise ValueError(f"expected exactly two color-4 cells, found {len(points)}")

    (r1, c1), (r2, c2) = points
    if (r1 + r2) % 2 or (c1 + c2) % 2:
        raise ValueError("the two markers do not have an integer grid-cell midpoint")

    out = [[0 for _ in range(cols)] for _ in range(rows)]
    out[(r1 + r2) // 2][(c1 + c2) // 2] = 8
    return out
