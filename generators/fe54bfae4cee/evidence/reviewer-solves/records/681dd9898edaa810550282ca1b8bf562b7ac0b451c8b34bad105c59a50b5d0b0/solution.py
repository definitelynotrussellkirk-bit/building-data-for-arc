def solve(grid):
    """Fill a one-cell gap between matching nonzero endpoints."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue

            if col + 2 < width and grid[row][col + 1] == 0 and grid[row][col + 2] == color:
                out[row][col + 1] = color

            if row + 2 < height and grid[row + 1][col] == 0 and grid[row + 2][col] == color:
                out[row + 1][col] = color

    return out
