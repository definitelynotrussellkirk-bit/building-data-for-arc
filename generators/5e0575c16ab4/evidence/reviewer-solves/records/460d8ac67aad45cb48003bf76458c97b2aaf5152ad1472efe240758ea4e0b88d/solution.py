from collections import Counter


def solve(grid):
    """Connect a color's two horizontal endpoints when they are its only cells."""
    out = [row[:] for row in grid]
    counts = Counter(value for row in grid for value in row if value != 0)

    for row_index, row in enumerate(grid):
        by_color = {}
        for column, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append(column)

        for color, columns in by_color.items():
            if counts[color] != 2 or len(columns) != 2:
                continue
            left, right = columns
            if all(row[column] == 0 for column in range(left + 1, right)):
                for column in range(left + 1, right):
                    out[row_index][column] = color

    return out
