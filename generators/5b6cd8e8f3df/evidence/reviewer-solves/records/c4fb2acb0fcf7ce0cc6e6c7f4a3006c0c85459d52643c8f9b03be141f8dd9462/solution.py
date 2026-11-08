def solve(grid):
    """Expand every nonzero cell into an orthogonal radius-one plus."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for drow, dcol in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                out_row = row + drow
                out_col = col + dcol
                if 0 <= out_row < height and 0 <= out_col < width:
                    result[out_row][out_col] = color

    return result
