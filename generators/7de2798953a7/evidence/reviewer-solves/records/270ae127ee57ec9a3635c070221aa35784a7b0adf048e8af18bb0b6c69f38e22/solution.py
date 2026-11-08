"""Visible-example solution for task 7de2798953a7."""


def solve(grid):
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        occupied = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(occupied) != 2:
            continue
        (left, left_colour), (right, right_colour) = occupied
        if left_colour != right_colour:
            continue
        for column in range(left + 1, right, 2):
            output[row_index][column] = left_colour
    return output
