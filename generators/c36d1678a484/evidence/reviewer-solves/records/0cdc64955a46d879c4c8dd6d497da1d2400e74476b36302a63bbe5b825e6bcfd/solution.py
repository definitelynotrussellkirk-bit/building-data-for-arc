"""Visible-example solution for ARC task c36d1678a484."""


def solve(grid):
    """Fill a row with 7 only when its sole nonzero entry is one 7."""
    output = [list(row) for row in grid]
    for index, row in enumerate(grid):
        nonzero = [value for value in row if value != 0]
        if nonzero == [7]:
            output[index] = [7] * len(row)
    return output
