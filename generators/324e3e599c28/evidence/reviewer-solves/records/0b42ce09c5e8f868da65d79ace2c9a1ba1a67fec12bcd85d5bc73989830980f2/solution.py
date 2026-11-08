"""Visible-example solution for blind task 324e3e599c28."""


def solve(grid):
    """Copy every colored cell through the unique color-9 point by 180° rotation."""
    out = [row[:] for row in grid]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one color-9 pivot, found {len(markers)}")

    pivot_r, pivot_c = markers[0]
    height = len(grid)
    width = len(grid[0]) if height else 0
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            reflected_r = 2 * pivot_r - r
            reflected_c = 2 * pivot_c - c
            if 0 <= reflected_r < height and 0 <= reflected_c < width:
                out[reflected_r][reflected_c] = value

    return out
