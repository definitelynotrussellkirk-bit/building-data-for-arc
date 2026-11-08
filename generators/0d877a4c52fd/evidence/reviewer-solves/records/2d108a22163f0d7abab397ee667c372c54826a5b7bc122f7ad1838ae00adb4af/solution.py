from collections import defaultdict


def solve(grid):
    """Complete the missing corner of every monochromatic axis-aligned rectangle."""
    output = [row[:] for row in grid]
    cells_by_color = defaultdict(list)

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                cells_by_color[color].append((row_index, column_index))

    for color, cells in cells_by_color.items():
        rows = {row for row, _ in cells}
        columns = {column for _, column in cells}
        if len(cells) != 3 or len(rows) != 2 or len(columns) != 2:
            continue

        occupied = set(cells)
        missing = [
            (row, column)
            for row in rows
            for column in columns
            if (row, column) not in occupied
        ]
        if len(missing) == 1:
            row, column = missing[0]
            output[row][column] = color

    return output
