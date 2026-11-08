def solve(grid):
    """Recolor blue cells by agreement with reflection across the horizontal axis."""
    height = len(grid)
    return [
        [
            0 if value == 0 else (2 if grid[height - 1 - r][c] == value else 5)
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]
