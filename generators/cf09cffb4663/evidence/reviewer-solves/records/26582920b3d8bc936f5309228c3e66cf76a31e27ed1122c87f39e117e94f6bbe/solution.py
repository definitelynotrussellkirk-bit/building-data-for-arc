def solve(grid):
    """Mark every true four-way crossing of the color-1 strokes with color 2."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if (
                grid[row][col] == 1
                and grid[row - 1][col] == 1
                and grid[row + 1][col] == 1
                and grid[row][col - 1] == 1
                and grid[row][col + 1] == 1
            ):
                out[row][col] = 2
    return out
