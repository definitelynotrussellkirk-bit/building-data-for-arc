def solve(grid):
    """Count sliding 2x2 all-1 windows and encode the count in a 1x5 bar."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    count = sum(
        grid[row][col] == 1
        and grid[row + 1][col] == 1
        and grid[row][col + 1] == 1
        and grid[row + 1][col + 1] == 1
        for row in range(height - 1)
        for col in range(width - 1)
    )
    return [[1 if col < count else 0 for col in range(5)]]
