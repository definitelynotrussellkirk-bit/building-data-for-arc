"""Visible-example-only solution for blind task 204eaaff6c24."""


def solve(grid):
    """Pack every non-background cell into a single row, in row-major order."""
    packed = [value for row in grid for value in row if value != 0]
    return [packed]
