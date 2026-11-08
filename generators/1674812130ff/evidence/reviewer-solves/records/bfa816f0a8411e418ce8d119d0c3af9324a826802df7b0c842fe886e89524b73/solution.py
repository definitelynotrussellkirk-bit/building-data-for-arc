"""Blind solution inferred from visible examples only."""


def solve(grid):
    """Complete the half-turn copy across the marked center.

    A vertical line of 4s and a horizontal marker row containing 8s meet at
    the rotation center.  The colored construction on the left is copied to
    the right by a 180-degree rotation around that center.
    """
    out = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0])

    # The divider is the column containing the most 4s.
    divider = max(range(w), key=lambda c: sum(grid[r][c] == 4 for r in range(h)))

    # The center row is marked by 8 at the divider and typically at both ends.
    marker_rows = [r for r in range(h) if grid[r][divider] == 8]
    if marker_rows:
        center_row = max(marker_rows, key=lambda r: sum(v == 8 for v in grid[r]))
    else:
        center_row = max(range(h), key=lambda r: sum(v == 8 for v in grid[r]))

    # Rotate the complete left half (including background and the left marker)
    # into the right half.  The marked divider itself remains unchanged.
    for r in range(h):
        rr = 2 * center_row - r
        if not (0 <= rr < h):
            continue
        for c in range(divider):
            cc = 2 * divider - c
            if 0 <= cc < w:
                out[rr][cc] = grid[r][c]

    return out
