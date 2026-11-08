def solve(grid):
    """Paint the outer border with the sole nonzero input color."""
    color = next(value for row in grid for value in row if value != 0)
    height = len(grid)
    width = len(grid[0])
    return [
        [
            color
            if row in (0, height - 1) or col in (0, width - 1)
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]
