def solve(grid):
    """Append a horizontal mirror image of each input row."""
    return [list(row) + list(reversed(row)) for row in grid]
