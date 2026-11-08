def solve(grid):
    """Fill a one-cell horizontal gap between equal nonzero colors."""
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c in range(1, len(row) - 1):
            if row[c] == 0 and row[c - 1] != 0 and row[c - 1] == row[c + 1]:
                result[r][c] = row[c - 1]
    return result
