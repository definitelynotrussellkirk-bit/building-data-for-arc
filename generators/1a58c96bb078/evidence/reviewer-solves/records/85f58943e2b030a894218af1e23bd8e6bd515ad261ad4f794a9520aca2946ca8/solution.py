"""Visible-example solution for the generated column-legend puzzle."""


def solve(grid):
    output = [row[:] for row in grid]
    if not output:
        return output
    for row in range(1, len(output)):
        for col, value in enumerate(grid[row]):
            header = grid[0][col]
            if value == 8 and header != 0:
                output[row][col] = header
    return output
