"""Infer the output by reflecting across the visible horizontal 9-valued line."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    axes = [
        r for r, row in enumerate(grid)
        if len(row) == width and all(value == 9 for value in row)
    ]
    if len(axes) != 1:
        raise ValueError("Expected one full horizontal row of color 9")

    axis = axes[0]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for source_row, row in enumerate(grid):
        destination_row = 2 * axis - source_row
        if 0 <= destination_row < height:
            output[destination_row] = list(row)
    return output
