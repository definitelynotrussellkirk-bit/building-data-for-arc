from collections import Counter


def solve(grid):
    """Expand the lone non-background cell to its nearest corner.

    The vertical and horizontal directions are selected independently.  Exact
    ties go upward/leftward, matching the centered training example.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    markers = [
        (row_index, column_index, value)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value != background
    ]
    if not markers:
        return [row[:] for row in grid]

    marker_row, marker_column, marker_color = markers[0]

    row_start, row_stop = (
        (0, marker_row + 1)
        if marker_row <= height - 1 - marker_row
        else (marker_row, height)
    )
    column_start, column_stop = (
        (0, marker_column + 1)
        if marker_column <= width - 1 - marker_column
        else (marker_column, width)
    )

    result = [[background for _ in range(width)] for _ in range(height)]
    for row_index in range(row_start, row_stop):
        for column_index in range(column_start, column_stop):
            result[row_index][column_index] = marker_color
    return result
