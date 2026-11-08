def solve(grid):
    """Reflect the colored pattern on the left across the full blue divider."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    divider_columns = [
        column
        for column in range(width)
        if all(grid[row][column] == 8 for row in range(height))
    ]
    if not divider_columns:
        return output

    divider = divider_columns[0]
    for row in range(height):
        for column in range(divider):
            color = grid[row][column]
            if color == 0 or color == 8:
                continue
            reflected = 2 * divider - column
            if reflected < width:
                output[row][reflected] = color

    return output
