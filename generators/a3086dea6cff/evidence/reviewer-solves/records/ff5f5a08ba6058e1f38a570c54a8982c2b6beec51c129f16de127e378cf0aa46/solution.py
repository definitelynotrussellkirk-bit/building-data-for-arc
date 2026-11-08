"""Visible-example-only solution for blind ARC task a3086dea6cff."""


def solve(grid):
    """Connect exactly-two equal-colored markers when row- or column-aligned.

    Vertical segments are painted first and horizontal segments second, matching
    the visible examples' crossing precedence.
    """
    out = [row[:] for row in grid]
    cells = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                cells.setdefault(value, []).append((r, c))

    pairs = []
    for value, positions in cells.items():
        if len(positions) != 2:
            continue
        (r1, c1), (r2, c2) = positions
        if c1 == c2:
            pairs.append((0, value, r1, c1, r2, c2))
        elif r1 == r2:
            pairs.append((1, value, r1, c1, r2, c2))

    # Visible intersections consistently preserve the horizontal segment.
    for _, value, r1, c1, r2, c2 in sorted(pairs):
        if c1 == c2:
            lo, hi = sorted((r1, r2))
            for r in range(lo, hi + 1):
                out[r][c1] = value
        else:
            lo, hi = sorted((c1, c2))
            for c in range(lo, hi + 1):
                out[r1][c] = value
    return out
