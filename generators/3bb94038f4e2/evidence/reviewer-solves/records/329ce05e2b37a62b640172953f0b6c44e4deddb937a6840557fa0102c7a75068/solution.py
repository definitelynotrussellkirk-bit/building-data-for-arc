"""Visible-example solution for blind task 3bb94038f4e2."""


def solve(grid):
    """Fill each horizontal one-cell gap in a 1,0,1 pattern with color 1.

    The decision is made from the original grid so newly filled cells do not
    trigger additional propagation.
    """
    if not grid:
        return []

    result = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        for column in range(1, len(row) - 1):
            if row[column - 1] == 1 and row[column] == 0 and row[column + 1] == 1:
                result[row_index][column] = 1
    return result
