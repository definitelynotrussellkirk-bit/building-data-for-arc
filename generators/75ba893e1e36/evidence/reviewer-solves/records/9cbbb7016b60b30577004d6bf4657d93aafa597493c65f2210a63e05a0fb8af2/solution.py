def solve(grid):
    """Repeat each visible row as reversed, original, reversed, original."""
    return [(list(row)[::-1] + list(row)) * 2 for row in grid]
