from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Place two diagonal copies and extend meaningful blank rows in green.

    The output is a 2-by-2 canvas: the input appears in the top-left and
    bottom-right quadrants.  A completely blank input row is a horizontal
    separator when there is still colored content below it; each such row is
    extended across the full output width with color 3 in both copies.
    Trailing blank padding remains blank.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    output = [[0 for _ in range(2 * width)] for _ in range(2 * height)]

    for row_index, row in enumerate(grid):
        output[row_index][:width] = row[:]
        output[height + row_index][width:] = row[:]

    last_nonblank_row = max(
        (row_index for row_index, row in enumerate(grid) if any(cell != 0 for cell in row)),
        default=-1,
    )
    separator = [3] * (2 * width)
    for row_index in range(last_nonblank_row):
        if all(cell == 0 for cell in grid[row_index]):
            output[row_index] = separator[:]
            output[height + row_index] = separator[:]

    return output
