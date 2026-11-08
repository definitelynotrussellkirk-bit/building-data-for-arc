def solve(grid):
    """Copy every nonzero cell to its horizontal mirror, retaining sources."""
    output = [list(row) for row in grid]
    width = len(output[0]) if output else 0
    for row_index, row in enumerate(grid):
        for column, value in enumerate(row):
            if value != 0:
                output[row_index][width - 1 - column] = value
    return output
