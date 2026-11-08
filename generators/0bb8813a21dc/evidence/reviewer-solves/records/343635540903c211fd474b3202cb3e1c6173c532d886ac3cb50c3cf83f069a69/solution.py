def solve(grid):
    """Recolor every nonzero cell in a row with that row's first nonzero color."""
    result = []
    for row in grid:
        leader = next((value for value in row if value != 0), 0)
        result.append([leader if value != 0 else 0 for value in row])
    return result
