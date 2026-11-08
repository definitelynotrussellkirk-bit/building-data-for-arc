"""Visible-example solution for ARC task 9fbd0923e6ae."""
from copy import deepcopy


def solve(grid):
    target = grid[0][0]
    height = len(grid)
    width = len(grid[0])
    output = deepcopy(grid)

    full_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    full_rows = [
        row
        for row in range(height)
        if all(grid[row][col] == 5 for col in range(width))
    ]

    if full_columns:
        axis = full_columns[0]
        for row in range(height):
            for col in range(width):
                if grid[row][col] == target and (row, col) != (0, 0):
                    reflected = 2 * axis - col
                    if 0 <= reflected < width:
                        output[row][reflected] = target
    elif full_rows:
        axis = full_rows[0]
        for row in range(height):
            for col in range(width):
                if grid[row][col] == target and (row, col) != (0, 0):
                    reflected = 2 * axis - row
                    if 0 <= reflected < height:
                        output[reflected][col] = target
    return output
