from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Connect the red cell to the green cell with an azure L-shaped path.

    The horizontal leg lies on the red cell's row.  The vertical leg lies on
    the green cell's column.  Existing colored cells are preserved.
    """
    out = [row[:] for row in grid]
    red = None
    green = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                red = (r, c)
            elif value == 3:
                green = (r, c)

    if red is None or green is None:
        return out

    red_r, red_c = red
    green_r, green_c = green

    for c in range(min(red_c, green_c), max(red_c, green_c) + 1):
        if out[red_r][c] == 0:
            out[red_r][c] = 8

    for r in range(min(red_r, green_r), max(red_r, green_r) + 1):
        if out[r][green_c] == 0:
            out[r][green_c] = 8

    return out
