from collections import defaultdict


def solve(grid):
    """Connect each same-colored endpoint pair with an upper-row-first L path.

    Vertical legs are painted before horizontal legs because the visible
    demonstrations show horizontal segments on top at crossings. Original
    nonzero endpoint cells are restored at the end.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [row[:] for row in grid]

    positions = defaultdict(list)
    for row_index, row in enumerate(grid):
        if len(row) != width:
            raise ValueError("grid must be rectangular")
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    paths = []
    for color, endpoints in positions.items():
        if len(endpoints) != 2:
            raise ValueError(f"color {color!r} must occur exactly twice")
        upper, lower = sorted(endpoints, key=lambda point: (point[0], point[1]))
        paths.append((color, upper, lower))

    # Paint the lower endpoint's column from the upper row to the lower row.
    for color, (upper_row, _), (lower_row, lower_column) in paths:
        for row_index in range(upper_row, lower_row + 1):
            output[row_index][lower_column] = color

    # Paint the upper row between endpoint columns; this wins at crossings.
    for color, (upper_row, upper_column), (_, lower_column) in paths:
        left, right = sorted((upper_column, lower_column))
        for column_index in range(left, right + 1):
            output[upper_row][column_index] = color

    # The two marked cells are defining endpoints, not disposable path pixels.
    for color, endpoints in positions.items():
        for row_index, column_index in endpoints:
            output[row_index][column_index] = color

    return output
