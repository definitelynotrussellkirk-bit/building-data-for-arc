def solve(grid):
    """Copy each nonzero cell across the horizontal midline into an empty mate.

    Existing nonzero cells have priority: a mirrored value is written only when
    the destination cell is zero.
    """
    height = len(grid)
    result = [row[:] for row in grid]
    for row, values in enumerate(grid):
        mirror_row = height - 1 - row
        for col, value in enumerate(values):
            if value == 0 and grid[mirror_row][col] != 0:
                result[row][col] = grid[mirror_row][col]
    return result
