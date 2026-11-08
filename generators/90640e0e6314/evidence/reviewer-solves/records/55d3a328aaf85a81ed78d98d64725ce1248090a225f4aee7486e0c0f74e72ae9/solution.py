def solve(grid):
    """Mirror the input across adjoining vertical and horizontal seams."""
    bottom = [row[::-1] + list(row) for row in grid]
    return [row[:] for row in reversed(bottom)] + bottom
