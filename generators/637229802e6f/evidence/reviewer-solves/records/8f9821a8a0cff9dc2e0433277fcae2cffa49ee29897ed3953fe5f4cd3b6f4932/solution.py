"""Visible-example solution for ARC task 637229802e6f."""


def solve(grid):
    """Fill the 2x2 quadrant containing the unique red (2) marker."""
    height = len(grid)
    width = len(grid[0])
    marker = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    )
    row_half = height // 2
    col_half = width // 2
    row_start = 0 if marker[0] < row_half else row_half
    col_start = 0 if marker[1] < col_half else col_half

    output = [[6 for _ in range(width)] for _ in range(height)]
    for row in range(row_start, height if row_start else row_half):
        for col in range(col_start, width if col_start else col_half):
            output[row][col] = 2
    return output
