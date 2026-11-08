def solve(grid):
    """Replace every input cell with a 4x4 block of the same color."""
    return [
        [value for value in row for _ in range(4)]
        for row in grid
        for _ in range(4)
    ]
