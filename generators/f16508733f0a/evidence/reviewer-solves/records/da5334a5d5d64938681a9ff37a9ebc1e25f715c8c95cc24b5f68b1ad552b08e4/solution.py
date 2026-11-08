def solve(grid):
    """Complete every original monochrome 2x2 block missing one cell.

    The scan is deliberately based on the immutable input, so a newly filled
    cell cannot trigger a cascade into neighboring 2x2 blocks.
    """
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height = len(source)
    width = len(source[0]) if height else 0

    for row in range(height - 1):
        for col in range(width - 1):
            cells = [
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            ]
            values = [source[r][c] for r, c in cells]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                missing_index = values.index(0)
                missing_row, missing_col = cells[missing_index]
                output[missing_row][missing_col] = nonzero[0]

    return output
