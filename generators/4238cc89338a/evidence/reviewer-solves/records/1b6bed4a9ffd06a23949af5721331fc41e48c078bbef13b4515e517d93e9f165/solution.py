"""Visible-example solution for generated task 4238cc89338a."""


def _cells(grid, color):
    return [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == color
    ]


def _row_counts(cells):
    first = min(row for row, _ in cells)
    last = max(row for row, _ in cells)
    return [sum(row == current for row, _ in cells) for current in range(first, last + 1)]


def _column_counts(cells):
    first = min(column for _, column in cells)
    last = max(column for _, column in cells)
    return [
        sum(column == current for _, column in cells)
        for current in range(first, last + 1)
    ]


def solve(grid):
    """Cross blue row counts with red column counts to make a color-8 grid."""
    blue_rows = _row_counts(_cells(grid, 1))
    red_columns = _column_counts(_cells(grid, 2))
    return [
        [
            8 if column_index < blue_rows[row_index]
            and row_index < red_columns[column_index]
            else 0
            for column_index in range(len(red_columns))
        ]
        for row_index in range(len(blue_rows))
    ]
