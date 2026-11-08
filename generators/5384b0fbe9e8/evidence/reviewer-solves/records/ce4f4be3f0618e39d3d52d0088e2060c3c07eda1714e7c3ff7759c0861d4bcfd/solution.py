def solve(grid):
    height = len(grid)
    width = len(grid[0])

    divider_columns = [
        column
        for column in range(width)
        if grid[0][column] != 0
        and all(grid[row][column] == grid[0][column] for row in range(height))
    ]
    if len(divider_columns) != 1:
        raise ValueError("expected one complete nonzero vertical divider")

    divider = divider_columns[0]
    output = [list(row) for row in grid]
    for row in range(height):
        for column in range(divider):
            reflected = 2 * divider - column
            if reflected < width:
                output[row][reflected] = grid[row][column]
    return output
