def solve(grid):
    """Move every nonzero cell to the top of its column, stably."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    result = [[0 for _ in range(width)] for _ in range(height)]

    for col in range(width):
        values = [grid[row][col] for row in range(height) if grid[row][col] != 0]
        for row, value in enumerate(values):
            result[row][col] = value

    return result
