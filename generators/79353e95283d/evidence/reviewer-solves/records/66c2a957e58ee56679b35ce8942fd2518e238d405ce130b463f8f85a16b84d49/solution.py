def solve(grid):
    """Mark positions occupied in both aligned panels, discarding the separator."""
    return [
        [2 if row[column] == 1 and row[column + 4] == 1 else 0
         for column in range(3)]
        for row in grid
    ]
