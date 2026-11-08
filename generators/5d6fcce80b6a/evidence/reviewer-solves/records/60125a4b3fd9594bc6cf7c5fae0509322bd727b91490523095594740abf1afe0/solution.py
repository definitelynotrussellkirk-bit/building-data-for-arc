from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Duplicate the input on the main block diagonal and extend active blank rows.

    The output is a 2x2 block canvas.  The original grid is copied into the
    upper-left and lower-right blocks.  A completely blank source row that lies
    at or before the last non-blank row is an in-content separator, so both of
    its duplicated output rows become a full-width green (3) line.  Trailing
    blank padding remains blank.
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

    nonblank_rows = [
        row_index
        for row_index, row in enumerate(grid)
        if any(cell != 0 for cell in row)
    ]
    if nonblank_rows:
        last_nonblank = nonblank_rows[-1]
        separator = [3] * (2 * width)
        for row_index in range(last_nonblank + 1):
            if all(cell == 0 for cell in grid[row_index]):
                output[row_index] = separator[:]
                output[height + row_index] = separator[:]

    return output
