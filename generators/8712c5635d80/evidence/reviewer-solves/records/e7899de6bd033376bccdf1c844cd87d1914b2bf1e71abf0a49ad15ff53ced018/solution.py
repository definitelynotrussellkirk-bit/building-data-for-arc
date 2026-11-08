from copy import deepcopy


def solve(grid):
    """Copy the left-panel foreground into the matching right-panel coordinates.

    The panels are separated by a full-height color-9 column.  The right panel's
    border color is also the paint color for the copied silhouette.
    """
    h = len(grid)
    w = len(grid[0])
    sep = next(
        c for c in range(w)
        if all(grid[r][c] == 9 for r in range(h))
    )

    paint = next(
        grid[r][c]
        for r in range(h)
        for c in range(sep + 1, w)
        if grid[r][c] not in (0, 9)
    )

    out = deepcopy(grid)
    right0 = sep + 1
    for r in range(h):
        for c in range(sep):
            if grid[r][c] != 0:
                out[r][right0 + c] = paint
    return out
