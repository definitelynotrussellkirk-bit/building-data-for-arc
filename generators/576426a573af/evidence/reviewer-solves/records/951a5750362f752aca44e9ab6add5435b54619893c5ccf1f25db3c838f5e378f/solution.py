def solve(grid):
    height = len(grid)
    return [
        [value if value != 0 else grid[height - 1 - row][col]
         for col, value in enumerate(values)]
        for row, values in enumerate(grid)
    ]
