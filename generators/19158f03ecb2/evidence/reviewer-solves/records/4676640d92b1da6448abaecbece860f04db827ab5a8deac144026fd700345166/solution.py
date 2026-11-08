def solve(grid):
    """Append a left-right reflection of every row."""
    return [list(row) + list(reversed(row)) for row in grid]
