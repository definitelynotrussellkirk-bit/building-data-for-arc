from copy import deepcopy


def solve(grid):
    """Recolor each nonzero payload cell by its row's nonzero first cell."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        header = row[0]
        if header == 0:
            continue
        for col_index in range(1, len(row)):
            if row[col_index] != 0:
                output[row_index][col_index] = header
    return output
