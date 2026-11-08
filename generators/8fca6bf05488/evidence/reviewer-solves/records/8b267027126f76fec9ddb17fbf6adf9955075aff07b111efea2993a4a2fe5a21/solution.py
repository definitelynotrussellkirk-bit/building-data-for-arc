def solve(grid):
    """Extend each nonzero source straight downward to the bottom edge.

    Sources are processed in row-major order, so a lower source in the same
    column overwrites the suffix below it.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color == 0:
                continue
            for target_row in range(row, height):
                out[target_row][column] = color
    return out
