from collections import defaultdict


def _sign(value):
    return (value > 0) - (value < 0)


def solve(grid):
    """Draw the longest same-color straight segment, using color 8."""
    positions = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    candidates = []
    for color, points in positions.items():
        if len(points) != 2:
            continue
        (row_a, column_a), (row_b, column_b) = points
        delta_row = row_b - row_a
        delta_column = column_b - column_a
        if not (
            delta_row == 0
            or delta_column == 0
            or abs(delta_row) == abs(delta_column)
        ):
            continue
        length = max(abs(delta_row), abs(delta_column))
        candidates.append((length, color, points))

    if not candidates:
        raise ValueError("expected at least one aligned pair of equal nonzero colors")

    _, _, ((row, column), (end_row, end_column)) = max(candidates)
    step_row = _sign(end_row - row)
    step_column = _sign(end_column - column)

    output = [[0 for _ in input_row] for input_row in grid]
    while True:
        output[row][column] = 8
        if (row, column) == (end_row, end_column):
            break
        row += step_row
        column += step_column
    return output
