def solve(grid):
    """Mark the center of every orthogonal four-way cross of color 3."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if (
                grid[row][col] == 0
                and grid[row - 1][col] == 3
                and grid[row + 1][col] == 3
                and grid[row][col - 1] == 3
                and grid[row][col + 1] == 3
            ):
                out[row][col] = 8

    return out
