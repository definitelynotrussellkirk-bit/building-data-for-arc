"""Visible-example solution for review task aea1d569d78b."""
from copy import deepcopy


def solve(grid):
    original = deepcopy(grid)
    output = deepcopy(grid)
    height = len(original)
    width = len(original[0])

    for row in range(height):
        blue_columns = [column for column in range(width) if original[row][column] == 1]
        if len(blue_columns) != 2:
            continue
        left, right = blue_columns
        if all(original[row][column] == 0 for column in range(left + 1, right)):
            for column in range(left + 1, right):
                output[row][column] = 3

    for column in range(width):
        blue_rows = [row for row in range(height) if original[row][column] == 1]
        if len(blue_rows) != 2:
            continue
        top, bottom = blue_rows
        if all(original[row][column] == 0 for row in range(top + 1, bottom)):
            for row in range(top + 1, bottom):
                output[row][column] = 3

    return output
