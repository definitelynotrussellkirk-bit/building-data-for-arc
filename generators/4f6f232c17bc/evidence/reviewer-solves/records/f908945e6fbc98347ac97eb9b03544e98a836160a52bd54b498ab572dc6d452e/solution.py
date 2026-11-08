"""Visible-example solution for the reviewer-authored lesson."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    divider_columns = [
        column
        for column in range(width)
        if all(grid[row][column] == 5 for row in range(height))
    ]
    if len(divider_columns) != 1:
        raise ValueError(
            f"expected exactly one full-height gray divider, found {divider_columns}"
        )
    divider = divider_columns[0]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, values in enumerate(grid):
        for column, value in enumerate(values):
            if value != 1:
                continue
            reflected_column = 2 * divider - column
            if 0 <= reflected_column < width:
                output[row][reflected_column] = 8
    return output
