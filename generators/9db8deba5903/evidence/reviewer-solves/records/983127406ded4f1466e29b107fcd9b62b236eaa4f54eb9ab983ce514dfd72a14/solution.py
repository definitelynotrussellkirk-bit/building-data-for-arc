def _rotate_ccw(grid):
    """Return a 90-degree counter-clockwise rotation of a rectangular grid."""
    return [list(column) for column in zip(*grid)][::-1]


def solve(grid):
    """Arrange four quarter-turns of the square input in a 2x2 pinwheel."""
    top_left = [row[:] for row in grid]
    top_right = _rotate_ccw(top_left)
    bottom_left = _rotate_ccw(top_right)
    bottom_right = _rotate_ccw(bottom_left)

    top = [left + right for left, right in zip(top_left, top_right)]
    bottom = [left + right for left, right in zip(bottom_left, bottom_right)]
    return top + bottom
