"""Visible-example solution for blind task 9db8deba5903."""


def _rotate_ccw(grid):
    """Return a 90-degree counter-clockwise rotation of a rectangular grid."""
    return [list(column) for column in zip(*grid)][::-1]


def _rotate_cw(grid):
    """Return a 90-degree clockwise rotation of a rectangular grid."""
    return [list(column) for column in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def solve(grid):
    """Tile the four quarter-turn orientations in rotational order.

    Visible examples place the original in the upper-left, the 90-degree
    counter-clockwise rotation in the upper-right, the 180-degree rotation in
    the lower-left, and the 90-degree clockwise rotation in the lower-right.
    """
    original = [list(row) for row in grid]
    ccw = _rotate_ccw(original)
    half = _rotate_180(original)
    cw = _rotate_cw(original)

    top = [left + right for left, right in zip(original, ccw)]
    bottom = [left + right for left, right in zip(half, cw)]
    return top + bottom
