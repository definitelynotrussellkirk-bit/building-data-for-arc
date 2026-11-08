from collections import Counter


def solve(grid):
    """Draw the corner-to-corner orthogonal path selected by the marker quadrant."""
    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    marker_positions = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value != background
    ]
    if len(marker_positions) != 1:
        raise ValueError("expected exactly one non-background marker")

    marker_row, marker_column = marker_positions[0]
    marker_value = grid[marker_row][marker_column]

    # A marker nearest either main-diagonal corner (top-left or bottom-right)
    # selects the opposite pair of corners.  The other two quadrants select
    # top-left to bottom-right.  The path always bends on the marker column.
    same_side_quadrant = (
        (marker_row < height / 2 and marker_column < width / 2)
        or (marker_row >= height / 2 and marker_column >= width / 2)
    )

    for row_index in range(height):
        output[row_index][marker_column] = 1

    if same_side_quadrant:
        for column_index in range(marker_column, width):
            output[0][column_index] = 1
        for column_index in range(0, marker_column + 1):
            output[height - 1][column_index] = 1
    else:
        for column_index in range(0, marker_column + 1):
            output[0][column_index] = 1
        for column_index in range(marker_column, width):
            output[height - 1][column_index] = 1

    output[marker_row][marker_column] = marker_value
    return output
