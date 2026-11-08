def solve(grid):
    """Rotate a rectangular ARC grid by 180 degrees."""
    return [list(reversed(row)) for row in reversed(grid)]
