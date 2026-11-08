def solve(grid):
    """Append each visible row's reverse, preserving every cell value."""
    return [list(row) + list(reversed(row)) for row in grid]
