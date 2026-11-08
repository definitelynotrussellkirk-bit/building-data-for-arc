"""Visible-example solution for blind task aea1d569d78b."""


def solve(grid):
    """Join unobstructed, axis-aligned pairs of blue cells with green."""
    source = [list(row) for row in grid]
    result = [row[:] for row in source]
    if not source:
        return result

    height = len(source)
    width = len(source[0])

    # Decide every segment from the unchanged input so crossing valid segments do
    # not accidentally block one another after the first segment is painted.
    segments = []

    for row in range(height):
        blue_columns = [column for column, value in enumerate(source[row]) if value == 1]
        for left_index, left in enumerate(blue_columns):
            for right in blue_columns[left_index + 1 :]:
                if all(source[row][column] == 0 for column in range(left + 1, right)):
                    segments.append((row, left + 1, row, right))

    for column in range(width):
        blue_rows = [row for row in range(height) if source[row][column] == 1]
        for top_index, top in enumerate(blue_rows):
            for bottom in blue_rows[top_index + 1 :]:
                if all(source[row][column] == 0 for row in range(top + 1, bottom)):
                    segments.append((top + 1, column, bottom, column))

    for row_start, column_start, row_stop, column_stop in segments:
        if row_start == row_stop:
            for column in range(column_start, column_stop):
                result[row_start][column] = 3
        else:
            for row in range(row_start, row_stop):
                result[row][column_start] = 3

    return result
