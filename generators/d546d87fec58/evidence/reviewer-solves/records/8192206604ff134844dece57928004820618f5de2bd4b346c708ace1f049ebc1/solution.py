def solve(grid):
    """Replace color-4 erasures from their horizontal/vertical reflection orbit."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 4:
                continue
            orbit = (
                (height - 1 - row, width - 1 - col),
                (row, width - 1 - col),
                (height - 1 - row, col),
            )
            output[row][col] = next(
                (grid[r][c] for r, c in orbit if grid[r][c] != 4),
                4,
            )
    return output
