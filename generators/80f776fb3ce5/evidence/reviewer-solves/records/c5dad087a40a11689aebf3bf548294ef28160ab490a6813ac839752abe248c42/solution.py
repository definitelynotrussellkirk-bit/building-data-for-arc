def solve(grid):
    """Fill background centers orthogonally enclosed by four blue cells."""
    out = [row[:] for row in grid]
    if not grid:
        return out

    height = len(grid)
    width = len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if (
                grid[row][col] == 0
                and grid[row - 1][col] == 1
                and grid[row + 1][col] == 1
                and grid[row][col - 1] == 1
                and grid[row][col + 1] == 1
            ):
                out[row][col] = 8
    return out
