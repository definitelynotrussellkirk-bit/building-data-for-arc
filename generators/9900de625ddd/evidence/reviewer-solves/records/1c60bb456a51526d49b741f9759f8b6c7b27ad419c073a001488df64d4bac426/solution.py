def solve(grid):
    """Keep cells whose complete 3-by-3 neighborhood has their color."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0] * width for _ in range(height)]
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            color = grid[row][col]
            if color and all(
                grid[r][c] == color
                for r in range(row - 1, row + 2)
                for c in range(col - 1, col + 2)
            ):
                result[row][col] = color
    return result
