def solve(grid):
    """Exchange the row and column coordinates of every visible cell."""
    return [list(column) for column in zip(*grid)]
