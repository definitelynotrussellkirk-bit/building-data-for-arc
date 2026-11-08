from __future__ import annotations


def _normalized_cells(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    cells = {
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == color
    }
    if not cells:
        return set()
    min_row = min(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    return {(row - min_row, column - min_column) for row, column in cells}


def _render(cells: set[tuple[int, int]]) -> list[list[int]]:
    if not cells:
        return [[0]]
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    max_column = max(column for _, column in cells)
    return [
        [
            8 if (row, column) in cells else 0
            for column in range(min_column, max_column + 1)
        ]
        for row in range(min_row, max_row + 1)
    ]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Combine the normalized color-1 and color-2 shapes as directed by the marker."""
    first = _normalized_cells(grid, 1)
    second = _normalized_cells(grid, 2)

    markers = {
        value
        for row in grid
        for value in row
        if value not in (0, 1, 2)
    }
    marker = next(iter(markers)) if len(markers) == 1 else None

    if marker == 3:
        result = first & second
    elif marker == 4:
        result = first | second
    else:
        result = first ^ second

    return _render(result)
