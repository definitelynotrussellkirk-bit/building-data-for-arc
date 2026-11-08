"""Apply the local red-neighbor condition inferred from the visible examples."""


def solve(grid):
    result = [row[:] for row in grid]
    for row in range(1, len(grid) - 1):
        for column in range(1, len(grid[0]) - 1):
            if (grid[row][column] == 0
                    and grid[row - 1][column] == 2
                    and grid[row + 1][column] == 2
                    and grid[row][column - 1] == 2
                    and grid[row][column + 1] == 2):
                result[row][column] = 4
    return result
