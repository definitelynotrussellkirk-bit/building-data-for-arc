from collections import defaultdict


def solve(grid):
    """Connect each pair of equal nonzero cells with a down-then-across L."""
    output = [row[:] for row in grid]
    positions = defaultdict(list)

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    for color, endpoints in positions.items():
        if len(endpoints) != 2:
            continue

        upper, lower = sorted(endpoints)
        upper_row, upper_column = upper
        lower_row, lower_column = lower

        for row_index in range(upper_row, lower_row + 1):
            output[row_index][upper_column] = color

        left = min(upper_column, lower_column)
        right = max(upper_column, lower_column)
        for column_index in range(left, right + 1):
            output[lower_row][column_index] = color

    return output
