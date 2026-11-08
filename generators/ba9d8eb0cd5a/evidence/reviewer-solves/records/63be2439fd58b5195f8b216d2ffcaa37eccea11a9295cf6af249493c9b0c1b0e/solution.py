def solve(grid):
    """Move each row's nonzero cells left, preserving their order."""
    result = []
    for row in grid:
        nonzero = [cell for cell in row if cell != 0]
        result.append(nonzero + [0] * (len(row) - len(nonzero)))
    return result
