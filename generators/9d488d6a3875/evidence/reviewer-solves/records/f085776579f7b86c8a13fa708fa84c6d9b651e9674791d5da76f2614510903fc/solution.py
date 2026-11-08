from collections import defaultdict


def solve(grid):
    """Join each same-colored pair with an axis-aligned solid segment."""
    result = [row[:] for row in grid]
    positions = defaultdict(list)

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    for color, endpoints in positions.items():
        if len(endpoints) != 2:
            continue

        (row_a, column_a), (row_b, column_b) = endpoints
        if row_a == row_b:
            left, right = sorted((column_a, column_b))
            for column in range(left, right + 1):
                result[row_a][column] = color
        elif column_a == column_b:
            top, bottom = sorted((row_a, row_b))
            for row in range(top, bottom + 1):
                result[row][column_a] = color

    return result
