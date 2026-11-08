from __future__ import annotations


def _spans(length: int, separators: list[int]) -> list[tuple[int, int]]:
    """Return half-open non-separator spans."""
    spans: list[tuple[int, int]] = []
    start = 0
    for separator in separators:
        if start < separator:
            spans.append((start, separator))
        start = separator + 1
    if start < length:
        spans.append((start, length))
    return spans


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Mark each separator-delimited panel containing at least two 6-cells."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separator_rows = [
        row_index
        for row_index, row in enumerate(grid)
        if all(value == 8 for value in row)
    ]
    separator_columns = [
        column_index
        for column_index in range(width)
        if all(grid[row_index][column_index] == 8 for row_index in range(height))
    ]

    row_spans = _spans(height, separator_rows)
    column_spans = _spans(width, separator_columns)

    return [
        [
            int(
                sum(
                    grid[row_index][column_index] == 6
                    for row_index in range(row_start, row_stop)
                    for column_index in range(column_start, column_stop)
                )
                >= 2
            )
            for column_start, column_stop in column_spans
        ]
        for row_start, row_stop in row_spans
    ]
