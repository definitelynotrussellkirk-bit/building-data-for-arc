def solve(grid):
    """Expand each original color-1 cell into a clipped 3x3 zero-only halo."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]
    seeds = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]

    for seed_row, seed_col in seeds:
        for row in range(max(0, seed_row - 1), min(height, seed_row + 2)):
            for col in range(max(0, seed_col - 1), min(width, seed_col + 2)):
                if grid[row][col] == 0:
                    result[row][col] = 1

    return result
