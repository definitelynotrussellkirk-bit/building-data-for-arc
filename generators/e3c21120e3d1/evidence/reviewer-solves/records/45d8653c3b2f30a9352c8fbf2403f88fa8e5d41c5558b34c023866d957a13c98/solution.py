def solve(grid):
    """Return the main-diagonal transpose of a rectangular grid."""
    return [list(column) for column in zip(*grid)]
