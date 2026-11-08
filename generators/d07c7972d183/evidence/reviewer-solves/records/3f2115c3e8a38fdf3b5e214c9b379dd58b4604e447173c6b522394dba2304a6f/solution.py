def solve(grid):
    height = len(grid)
    period = next(
        p for p in range(1, height + 1)
        if all(grid[row] == grid[row % p] for row in range(height))
    )
    return [
        [2 if color == 1 else color for color in grid[row % period]]
        for row in range(height + height // 2)
    ]
