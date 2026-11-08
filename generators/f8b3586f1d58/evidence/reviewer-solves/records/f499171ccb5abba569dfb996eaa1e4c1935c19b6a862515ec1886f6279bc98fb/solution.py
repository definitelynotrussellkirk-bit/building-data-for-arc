def solve(grid):
    output = [row[:] for row in grid]
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for column, color in enumerate(row):
            if color != 0:
                output[row_index][width - 1 - column] = color
    return output
