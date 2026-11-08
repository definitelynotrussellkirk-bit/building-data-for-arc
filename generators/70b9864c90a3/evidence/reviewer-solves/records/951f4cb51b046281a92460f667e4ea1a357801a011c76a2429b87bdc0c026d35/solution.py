def solve(grid):
    """Fill empty centers of 3x3 boxes with four equal nonzero corners."""
    result = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for top in range(height - 2):
        for left in range(width - 2):
            corner = grid[top][left]
            if corner == 0:
                continue
            if (
                grid[top][left + 2] == corner
                and grid[top + 2][left] == corner
                and grid[top + 2][left + 2] == corner
                and grid[top + 1][left + 1] == 0
            ):
                result[top + 1][left + 1] = corner

    return result
