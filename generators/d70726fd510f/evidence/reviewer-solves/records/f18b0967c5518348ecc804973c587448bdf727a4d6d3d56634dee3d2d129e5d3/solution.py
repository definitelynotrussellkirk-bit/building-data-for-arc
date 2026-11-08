def solve(grid):
    """Compare aligned nonzero occupancy across the full color-4 divider."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    separator = next(
        col
        for col in range(width)
        if all(grid[row][col] == 4 for row in range(height))
    )
    return [
        [
            2
            if (grid[row][col] != 0) != (grid[row][separator + 1 + col] != 0)
            else 0
            for col in range(separator)
        ]
        for row in range(height)
    ]
