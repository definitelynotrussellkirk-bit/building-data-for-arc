"""Visible-example solution for the crossing-rays puzzle."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    row_shooters = {row for row in range(1, height) if grid[row][0] == 2}
    col_shooters = {col for col in range(1, width) if grid[0][col] == 3}

    for row in range(1, height):
        for col in range(1, width):
            if grid[row][col] == 9:
                continue
            horizontal = row in row_shooters and all(
                grid[row][cursor] != 9 for cursor in range(1, col + 1)
            )
            vertical = col in col_shooters and all(
                grid[cursor][col] != 9 for cursor in range(1, row + 1)
            )
            if horizontal and vertical:
                output[row][col] = 8
            elif horizontal:
                output[row][col] = 2
            elif vertical:
                output[row][col] = 3
    return output
