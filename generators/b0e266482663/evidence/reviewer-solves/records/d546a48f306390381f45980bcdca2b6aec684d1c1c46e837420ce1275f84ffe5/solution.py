def solve(grid):
    """Propagate edge rays until blockers; crossings become cyan (8)."""
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    for row in range(1, height):
        for col in range(1, width):
            if grid[row][col] == 9:
                continue
            horizontal = grid[row][0] == 2 and all(
                grid[row][earlier] != 9 for earlier in range(1, col + 1)
            )
            vertical = grid[0][col] == 3 and all(
                grid[earlier][col] != 9 for earlier in range(1, row + 1)
            )
            if horizontal and vertical:
                output[row][col] = 8
            elif horizontal:
                output[row][col] = 2
            elif vertical:
                output[row][col] = 3
    return output
