def solve(grid):
    """Place an upside-down copy above the unchanged input."""
    return [row[:] for row in reversed(grid)] + [row[:] for row in grid]
