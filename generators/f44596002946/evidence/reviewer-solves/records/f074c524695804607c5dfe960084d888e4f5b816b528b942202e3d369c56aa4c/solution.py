"""Visible-example solution for the blind ARC task."""

from collections import defaultdict


def solve(grid):
    """Join exactly two equal-colored cells when they share a row or column.

    A color with any other multiplicity, or whose two cells are diagonal, is
    unchanged.  When two completed segments cross, the larger color number is
    visible, matching both crossings in the demonstrations.
    """
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions[color].append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r1][c] = max(out[r1][c], color)
        elif c1 == c2:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                out[r][c1] = max(out[r][c1], color)

    return out
