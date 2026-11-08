def solve(grid):
    """Use a nonzero cell on the left border to recolor its row's objects."""
    return [
        [row[0] if row[0] != 0 and color != 0 else color for color in row]
        for row in grid
    ]
