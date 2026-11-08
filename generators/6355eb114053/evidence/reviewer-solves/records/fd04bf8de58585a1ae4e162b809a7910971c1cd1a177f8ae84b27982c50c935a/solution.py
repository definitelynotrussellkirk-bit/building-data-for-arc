def solve(grid):
    """Fill the empty center of every monochromatic orthogonal cross."""
    output = [row[:] for row in grid]
    if not grid or not grid[0]:
        return output

    height = len(grid)
    width = len(grid[0])

    # Read only from the original grid so all completions happen simultaneously.
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            color = grid[row - 1][col]
            if color == 0:
                continue
            if (
                grid[row + 1][col] == color
                and grid[row][col - 1] == color
                and grid[row][col + 1] == color
            ):
                output[row][col] = color

    return output
