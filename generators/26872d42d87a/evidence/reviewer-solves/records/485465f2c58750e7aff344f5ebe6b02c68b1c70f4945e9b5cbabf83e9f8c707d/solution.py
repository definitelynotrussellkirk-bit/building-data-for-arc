from copy import deepcopy


def solve(grid):
    """Fill only one-cell horizontal gaps between two color-6 cells."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        for col in range(1, len(row) - 1):
            if row[col] == 0 and row[col - 1] == 6 and row[col + 1] == 6:
                output[row_index][col] = 6
    return output
