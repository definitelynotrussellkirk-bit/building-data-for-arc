"""Visible-example solution for blind task 5a215cef8bd1."""


def _rotate_clockwise(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def solve(grid):
    # The color-2 component is the motif.  Its square bounding box is copied
    # into the four quadrants of the answer, with a blank separator row/column.
    twos = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == 2
    ]
    if not twos:
        raise ValueError("expected a color-2 motif")

    min_row = min(row for row, _ in twos)
    max_row = max(row for row, _ in twos)
    min_column = min(column for _, column in twos)
    max_column = max(column for _, column in twos)
    height = max_row - min_row + 1
    width = max_column - min_column + 1
    if height != width:
        raise ValueError("expected a square motif bounding box")

    motif = [
        [1 if grid[row][column] == 2 else 0 for column in range(min_column, max_column + 1)]
        for row in range(min_row, max_row + 1)
    ]

    rotations = {1: motif}
    rotations[3] = _rotate_clockwise(rotations[1])
    rotations[4] = _rotate_clockwise(rotations[3])
    rotations[6] = [row[::-1] for row in rotations[1]]

    markers = {
        value: (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value in rotations
    }
    if set(markers) != set(rotations):
        raise ValueError("expected exactly one marker of each color 1, 3, 4, and 6")

    marker_rows = sorted({row for row, _ in markers.values()})
    marker_columns = sorted({column for _, column in markers.values()})
    if len(marker_rows) != 2 or len(marker_columns) != 2:
        raise ValueError("expected the four markers at the corners of a rectangle")

    size = height
    output = [[0 for _ in range(2 * size + 1)] for _ in range(2 * size + 1)]
    for color, (marker_row, marker_column) in markers.items():
        destination_row = 0 if marker_row == marker_rows[0] else size + 1
        destination_column = 0 if marker_column == marker_columns[0] else size + 1
        transformed = rotations[color]
        for row_offset, row in enumerate(transformed):
            for column_offset, value in enumerate(row):
                if value:
                    output[destination_row + row_offset][destination_column + column_offset] = 7

    return output
