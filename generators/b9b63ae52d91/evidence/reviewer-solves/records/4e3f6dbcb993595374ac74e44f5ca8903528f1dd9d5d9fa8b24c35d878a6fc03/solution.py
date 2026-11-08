def solve(grid):
    """Color occupied cells by whether their vertical reflection is occupied."""
    height = len(grid)
    return [
        [0 if value == 0 else (2 if grid[height - 1 - row][col] == value else 5)
         for col, value in enumerate(values)]
        for row, values in enumerate(grid)
    ]
