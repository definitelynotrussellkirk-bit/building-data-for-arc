def solve(grid):
    out = [row[:] for row in grid]
    for row in range(1, len(grid) - 1):
        for column in range(1, len(grid[0]) - 1):
            if (grid[row][column] == 0
                    and grid[row - 1][column] == 1
                    and grid[row + 1][column] == 1
                    and grid[row][column - 1] == 1
                    and grid[row][column + 1] == 1):
                out[row][column] = 8
    return out
