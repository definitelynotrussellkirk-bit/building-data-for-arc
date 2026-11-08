from __future__ import annotations


def solve(grid):
    """Copy the cyan shape around the green anchor onto every red marker."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    green = None
    reds = []
    cyans = []
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value == 3:
                green = (row_index, column_index)
            elif value == 2:
                reds.append((row_index, column_index))
            elif value == 8:
                cyans.append((row_index, column_index))

    if green is None:
        raise ValueError("expected one green anchor")

    anchor_row, anchor_column = green
    offsets = [
        (row_index - anchor_row, column_index - anchor_column)
        for row_index, column_index in cyans
    ]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for red_row, red_column in reds:
        for row_delta, column_delta in offsets:
            row_index = red_row + row_delta
            column_index = red_column + column_delta
            if 0 <= row_index < height and 0 <= column_index < width:
                output[row_index][column_index] = 8
    return output
