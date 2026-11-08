"""Visible-example solution for blind task 2f91d0756f23."""


def solve(grid):
    """Erase the unary markers and make that many quarter-turn copies.

    Color 9 is the rotation center.  Every other nonzero, non-1 cell is part
    of the seed motif.  The number of color-1 cells selects how many copies
    of the motif to keep: the original plus successive 90-degree clockwise
    rotations about the 9.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    marker_count = sum(value == 1 for row in grid for value in row)
    centers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(centers) != 1:
        raise ValueError(f"expected one color-9 center, found {len(centers)}")
    center_r, center_c = centers[0]

    motif = [
        (r - center_r, c - center_c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1, 9)
    ]

    # Remove the color-1 count markers.  Preserve the supplied seed motif and
    # center; generated copies are then painted from the original motif only.
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == 1:
                out[r][c] = 0

    for turn in range(marker_count):
        for delta_r, delta_c, value in motif:
            rotated_r, rotated_c = delta_r, delta_c
            for _ in range(turn % 4):
                rotated_r, rotated_c = rotated_c, -rotated_r
            r = center_r + rotated_r
            c = center_c + rotated_c
            if not (0 <= r < height and 0 <= c < width):
                raise ValueError("rotated motif leaves the grid")
            if out[r][c] not in (0, value):
                raise ValueError("rotated motif has a conflicting overlap")
            out[r][c] = value

    out[center_r][center_c] = 9
    return out
