def solve(grid):
    """Append a horizontal mirror image of the input grid."""
    return [list(row) + list(reversed(row)) for row in grid]
