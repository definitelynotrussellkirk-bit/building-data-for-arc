"""Solver inferred from the public ARC demonstrations."""


def solve(grid):
    """Complete each same-color axis-aligned rectangle missing one corner."""
    output = [row[:] for row in grid]
    positions = {}

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    for color, points in positions.items():
        if len(points) != 3:
            continue

        rows = sorted({row for row, _ in points})
        columns = sorted({column for _, column in points})
        if len(rows) != 2 or len(columns) != 2:
            continue

        occupied = set(points)
        missing = [
            (row, column)
            for row in rows
            for column in columns
            if (row, column) not in occupied
        ]
        if len(missing) != 1:
            continue

        row, column = missing[0]
        if output[row][column] == 0:
            output[row][column] = color

    return output
