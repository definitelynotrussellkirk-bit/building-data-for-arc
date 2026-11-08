def solve(grid):
    """Fill a zero cell with 4 when it is vertically bracketed by 7s."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(1, height - 1):
        for col in range(width):
            if grid[row][col] == 0 and grid[row - 1][col] == 7 and grid[row + 1][col] == 7:
                out[row][col] = 4
    return out
