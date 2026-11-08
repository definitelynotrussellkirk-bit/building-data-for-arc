def solve(grid):
    """Complete empty corners of red diagonals in otherwise empty 2x2 boxes."""
    out = [row[:] for row in grid]
    if not grid:
        return out

    height = len(grid)
    width = len(grid[0])
    to_green = set()

    for row in range(height - 1):
        for col in range(width - 1):
            top_left = grid[row][col]
            top_right = grid[row][col + 1]
            bottom_left = grid[row + 1][col]
            bottom_right = grid[row + 1][col + 1]

            if top_left == 2 and bottom_right == 2 and top_right == 0 and bottom_left == 0:
                to_green.add((row, col + 1))
                to_green.add((row + 1, col))
            elif top_right == 2 and bottom_left == 2 and top_left == 0 and bottom_right == 0:
                to_green.add((row, col))
                to_green.add((row + 1, col + 1))

    for row, col in to_green:
        out[row][col] = 3
    return out
