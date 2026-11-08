"""Visible-example solution for blind task e1e7c467196f."""


def solve(grid):
    """Apply the two-row lookup table at the upper left to the remaining grid.

    The contiguous nonzero prefix of row 0 contains source colors and the
    corresponding prefix of row 1 contains replacement colors.  The table is
    erased, while cells below it are recolored through that lookup.  Colors
    absent from the lookup are preserved.
    """
    if len(grid) < 2:
        return [row[:] for row in grid]

    width = min(len(grid[0]), len(grid[1]))
    table_width = 0
    while (
        table_width < width
        and grid[0][table_width] != 0
        and grid[1][table_width] != 0
    ):
        table_width += 1

    mapping = {
        grid[0][column]: grid[1][column]
        for column in range(table_width)
    }

    result = [row[:] for row in grid]
    result[0] = [0] * len(result[0])
    result[1] = [0] * len(result[1])

    for row in range(2, len(result)):
        for column, value in enumerate(result[row]):
            result[row][column] = mapping.get(value, value)

    return result
