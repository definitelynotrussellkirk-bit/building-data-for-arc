def solve(grid):
    """Continue the blue arithmetic line forward in red until the grid boundary."""
    output = [row[:] for row in grid]
    if not grid or not grid[0]:
        return output

    blue = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    )
    if len(blue) < 2:
        return output

    row_step = blue[1][0] - blue[0][0]
    col_step = blue[1][1] - blue[0][1]
    if row_step == 0 and col_step == 0:
        return output

    height = len(grid)
    width = len(grid[0])
    row = blue[-1][0] + row_step
    col = blue[-1][1] + col_step
    while 0 <= row < height and 0 <= col < width:
        output[row][col] = 2
        row += row_step
        col += col_step
    return output
