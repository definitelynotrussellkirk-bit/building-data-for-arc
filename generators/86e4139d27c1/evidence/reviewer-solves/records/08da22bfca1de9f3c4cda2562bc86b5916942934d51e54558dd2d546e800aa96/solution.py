from __future__ import annotations


def solve(grid):
    """Add a color-3 plus at the floor midpoint of the two color-1 cells."""
    out = [row[:] for row in grid]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    if len(markers) != 2:
        return out

    (r1, c1), (r2, c2) = markers
    center_r = (r1 + r2) // 2
    center_c = (c1 + c2) // 2

    height = len(out)
    width = len(out[0]) if height else 0
    for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        r = center_r + dr
        c = center_c + dc
        if 0 <= r < height and 0 <= c < width:
            out[r][c] = 3
    return out
