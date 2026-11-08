def solve(grid):
    """Move every nonzero cell in each row to the left, preserving row order."""
    result = []
    for row in grid:
        values = [cell for cell in row if cell != 0]
        result.append(values + [0] * (len(row) - len(values)))
    return result
