"""Visible-example solution for task 021fb6acf24f."""
from copy import deepcopy


def solve(grid):
    output = deepcopy(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        row0 = min(row for row, _ in cells)
        row1 = max(row for row, _ in cells)
        col0 = min(col for _, col in cells)
        col1 = max(col for _, col in cells)
        for row in range(row0, row1 + 1):
            for col in range(col0, col1 + 1):
                if output[row][col] == 0:
                    output[row][col] = color
    return output
