from copy import deepcopy


def solve(grid):
    """Copy each magenta cell across the full-height gray divider as cyan."""
    if not grid or not grid[0]:
        return deepcopy(grid)

    width = len(grid[0])
    dividers = [
        col
        for col in range(width)
        if all(len(row) == width and row[col] == 5 for row in grid)
    ]
    if len(dividers) != 1:
        raise ValueError("expected exactly one full-height gray divider")

    divider = dividers[0]
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        for col, value in enumerate(row[:divider]):
            if value != 6:
                continue
            mirror_col = 2 * divider - col
            if 0 <= mirror_col < width and output[row_index][mirror_col] == 0:
                output[row_index][mirror_col] = 8
    return output
