"""Visible-example solution; original grid values determine every fill."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    result = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            if (0 < col < width - 1 and grid[row][col - 1] != 0
                    and grid[row][col - 1] == grid[row][col + 1]):
                result[row][col] = grid[row][col - 1]
            if (0 < row < height - 1 and grid[row - 1][col] != 0
                    and grid[row - 1][col] == grid[row + 1][col]):
                result[row][col] = grid[row - 1][col]
    return result
