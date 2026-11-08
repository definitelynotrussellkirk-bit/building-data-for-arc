from copy import deepcopy


def solve(grid):
    """Fill a row's inclusive span only for exactly two equal nonzero markers."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        markers = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(markers) != 2:
            continue
        (left, left_color), (right, right_color) = markers
        if left_color != right_color or right - left < 2:
            continue
        for column in range(left, right + 1):
            out[row_index][column] = left_color
    return out
