def solve(grid):
    """Complete the grid by reflecting its top-left quadrant across both axes."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    return [
        [grid[min(row, height - 1 - row)][min(col, width - 1 - col)]
         for col in range(width)]
        for row in range(height)
    ]
