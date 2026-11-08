def solve(grid):
    """Mark aligned cells that are zero in both stacked input panels."""
    half_h = len(grid) // 2
    width = len(grid[0])
    return [
        [
            2 if grid[r][c] == 0 and grid[half_h + r][c] == 0 else 0
            for c in range(width)
        ]
        for r in range(half_h)
    ]
