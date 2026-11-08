def solve(grid):
    """Fill zero cells from vertically reflected input cells; keep occupied cells."""
    height = len(grid)
    return [[cell if cell != 0 else grid[height - 1 - row][col]
             for col, cell in enumerate(values)]
            for row, values in enumerate(grid)]
