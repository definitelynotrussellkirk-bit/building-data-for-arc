def solve(grid):
    """Remove the label borders and keep a row label where both labels match."""
    return [
        [grid[row][0] if grid[row][0] == grid[0][column] else 0
         for column in range(1, len(grid[0]))]
        for row in range(1, len(grid))
    ]
