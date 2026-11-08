from collections import defaultdict


def solve(grid):
    """Fill the inclusive bounding rectangle of every non-background color."""
    output = [row[:] for row in grid]
    positions = defaultdict(list)

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    for color, cells in positions.items():
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(column for _, column in cells)
        right = max(column for _, column in cells)
        for row_index in range(top, bottom + 1):
            for column_index in range(left, right + 1):
                output[row_index][column_index] = color

    return output
