from copy import deepcopy


def solve(grid):
    """Copy the color-2 object by the directed vector from 8 to 9.

    The translated cells are painted color 3.  Cells translated outside the
    canvas are ignored; all original cells remain otherwise unchanged.
    """
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])

    source = []
    marker8 = marker9 = None
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 2:
                source.append((row, col))
            elif value == 8:
                marker8 = (row, col)
            elif value == 9:
                marker9 = (row, col)

    if marker8 is None or marker9 is None:
        return out

    dr = marker9[0] - marker8[0]
    dc = marker9[1] - marker8[1]
    for row, col in source:
        target_row = row + dr
        target_col = col + dc
        if 0 <= target_row < height and 0 <= target_col < width:
            out[target_row][target_col] = 3
    return out
