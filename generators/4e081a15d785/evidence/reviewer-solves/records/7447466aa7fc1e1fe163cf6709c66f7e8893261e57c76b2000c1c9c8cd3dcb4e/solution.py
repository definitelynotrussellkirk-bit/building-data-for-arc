"""Compress consecutive runs of identical complete rows and columns."""


def solve(grid):
    """Keep one representative of each adjacent equal-row/equal-column run."""
    if not grid:
        return []

    rows = []
    for row in grid:
        if not rows or row != rows[-1]:
            rows.append(list(row))

    keep_columns = []
    previous_column = None
    for column_index in range(len(rows[0])):
        column = tuple(row[column_index] for row in rows)
        if column != previous_column:
            keep_columns.append(column_index)
        previous_column = column

    return [[row[column_index] for column_index in keep_columns] for row in rows]
