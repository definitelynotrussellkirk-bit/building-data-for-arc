"""Visible-example solution for blind task 9df67b512dad."""


def solve(grid):
    """Collapse border/interior bands to 3x3, keeping the last nonzero seen.

    The first and last input rows become the top and bottom output bands;
    every row between them becomes the middle band.  Columns are grouped the
    same way.  Within each of the nine bands, nonzero cells are read in normal
    row-major order and later colors overwrite earlier ones.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if height < 3 or width < 3:
        raise ValueError("this task expects at least a 3x3 input")

    row_ranges = ((0, 1), (1, height - 1), (height - 1, height))
    col_ranges = ((0, 1), (1, width - 1), (width - 1, width))

    output = [[0] * 3 for _ in range(3)]
    for out_r, (r0, r1) in enumerate(row_ranges):
        for out_c, (c0, c1) in enumerate(col_ranges):
            value = 0
            for r in range(r0, r1):
                for c in range(c0, c1):
                    if grid[r][c] != 0:
                        value = grid[r][c]
            output[out_r][out_c] = value
    return output
