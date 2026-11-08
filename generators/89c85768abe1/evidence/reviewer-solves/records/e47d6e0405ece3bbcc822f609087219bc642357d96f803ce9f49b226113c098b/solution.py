from collections import defaultdict


def solve(grid):
    """Fill the inclusive bounding box of every non-background color."""
    output = [row[:] for row in grid]
    cells = defaultdict(list)

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                cells[color].append((row_index, column_index))

    for color, coordinates in cells.items():
        rows = [row for row, _ in coordinates]
        columns = [column for _, column in coordinates]
        for row in range(min(rows), max(rows) + 1):
            for column in range(min(columns), max(columns) + 1):
                output[row][column] = color

    return output
