from copy import deepcopy


def solve(grid):
    """Mirror every nonzero top-panel cell across the full color-5 divider."""
    out = deepcopy(grid)
    divider_rows = [
        row_index
        for row_index, row in enumerate(grid)
        if row and all(value == 5 for value in row)
    ]
    if len(divider_rows) != 1:
        raise ValueError("expected exactly one full color-5 divider row")
    divider = divider_rows[0]
    for row in range(divider):
        mirror_row = 2 * divider - row
        if not 0 <= mirror_row < len(grid):
            raise ValueError("divider does not split equal-height panels")
        for col, value in enumerate(grid[row]):
            if value != 0:
                out[mirror_row][col] = value
    return out
