def solve(grid):
    """Preserve the input and copy every colored cell across the anti-diagonal."""
    n = len(grid)
    result = [row[:] for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                result[n - 1 - col][n - 1 - row] = value
    return result
