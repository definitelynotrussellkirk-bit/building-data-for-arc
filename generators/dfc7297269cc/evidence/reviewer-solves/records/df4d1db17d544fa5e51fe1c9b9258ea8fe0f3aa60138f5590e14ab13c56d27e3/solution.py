def solve(grid):
    """Fill a one-cell horizontal gap bracketed by the same nonzero color."""
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c in range(1, len(row) - 1):
            color = row[c - 1]
            if row[c] == 0 and color != 0 and row[c + 1] == color:
                result[r][c] = color
    return result
