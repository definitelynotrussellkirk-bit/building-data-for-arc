"""Visible-only solver for the three-panel symmetry task."""


def _rotate_ccw(grid):
    """Return a square grid rotated 90 degrees counter-clockwise."""
    return [list(row) for row in zip(*grid)][::-1]


def _flip_left_right(grid):
    return [row[::-1] for row in grid]


def _symmetries(grid):
    """Yield the eight dihedral symmetries of a square grid."""
    current = [row[:] for row in grid]
    for _ in range(4):
        yield current
        current = _rotate_ccw(current)

    current = _flip_left_right(grid)
    for _ in range(4):
        yield current
        current = _rotate_ccw(current)


def _mask(grid):
    return [[value != 0 for value in row] for row in grid]


def solve(grid):
    """Infer the first-to-second panel symmetry and apply it to panel three."""
    left = [row[0:4] for row in grid]
    middle = [row[5:9] for row in grid]
    right = [row[10:14] for row in grid]

    target = _mask(middle)
    for transformed_left, transformed_right in zip(
        _symmetries(_mask(left)), _symmetries(right)
    ):
        if transformed_left == target:
            return transformed_right

    raise ValueError("no square symmetry maps the first panel to the second")
