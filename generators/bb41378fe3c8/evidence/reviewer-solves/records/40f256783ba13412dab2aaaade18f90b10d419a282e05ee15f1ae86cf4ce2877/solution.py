"""Visible-example solution for bb41378fe3c8."""


def solve(grid):
    output = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2:
                continue
            target_row = row + 1
            target_col = col + 1
            if (
                target_row < height
                and target_col < width
                and grid[target_row][target_col] == 0
            ):
                output[target_row][target_col] = 5
    return output
