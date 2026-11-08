from __future__ import annotations


def _mask(panel: list[list[int]]) -> list[list[bool]]:
    return [[cell not in (0, 5) for cell in row] for row in panel]


def _close_rows(mask: list[list[bool]]) -> list[list[bool]]:
    result = [row[:] for row in mask]
    for row in result:
        occupied = [column for column, value in enumerate(row) if value]
        if len(occupied) >= 2:
            for column in range(occupied[0], occupied[-1] + 1):
                row[column] = True
    return result


def _close_columns(mask: list[list[bool]]) -> list[list[bool]]:
    result = [row[:] for row in mask]
    if not result:
        return result
    height = len(result)
    width = len(result[0])
    for column in range(width):
        occupied = [row for row in range(height) if result[row][column]]
        if len(occupied) >= 2:
            for row in range(occupied[0], occupied[-1] + 1):
                result[row][column] = True
    return result


def _crop(mask: list[list[bool]]) -> list[list[bool]]:
    occupied = [
        (row, column)
        for row, values in enumerate(mask)
        for column, value in enumerate(values)
        if value
    ]
    if not occupied:
        return []
    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(column for _, column in occupied)
    right = max(column for _, column in occupied)
    return [row[left : right + 1] for row in mask[top : bottom + 1]]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Infer whether the demonstration fills horizontal or vertical gaps.

    Two solid color-5 columns divide the input into a before panel, an after
    panel, and a target object.  The demonstrated operation closes every gap
    between the first and last occupied cell of each row or of each column.
    The same operation is applied to the cropped target and rendered in color 8.
    """

    height = len(grid)
    width = len(grid[0])
    separators = [
        column
        for column in range(width)
        if all(grid[row][column] == 5 for row in range(height))
    ]
    if len(separators) != 2:
        raise ValueError(f"expected exactly two full color-5 separators, got {separators}")

    first_separator, second_separator = separators
    panels = [
        [row[:first_separator] for row in grid],
        [row[first_separator + 1 : second_separator] for row in grid],
        [row[second_separator + 1 :] for row in grid],
    ]
    before, after, target = map(_mask, panels)

    row_closed = _close_rows(before)
    column_closed = _close_columns(before)
    row_matches = row_closed == after
    column_matches = column_closed == after

    if row_matches == column_matches:
        raise ValueError(
            "demonstration does not uniquely identify horizontal versus vertical gap filling"
        )

    target = _crop(target)
    transformed = _close_rows(target) if row_matches else _close_columns(target)
    return [[8 if value else 0 for value in row] for row in transformed]
