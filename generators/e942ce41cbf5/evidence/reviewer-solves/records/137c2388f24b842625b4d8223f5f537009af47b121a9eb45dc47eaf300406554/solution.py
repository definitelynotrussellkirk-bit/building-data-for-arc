"""Visible-example solution for e942ce41cbf5."""
from __future__ import annotations


def _normalize(cells):
    cells = list(cells)
    if not cells:
        return set()
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return {(row - min_row, col - min_col) for row, col in cells}


def _rotate_clockwise(cells):
    cells = _normalize(cells)
    if not cells:
        return set()
    height = max(row for row, _ in cells) + 1
    return _normalize((col, height - 1 - row) for row, col in cells)


def _flip_horizontal(cells):
    cells = _normalize(cells)
    if not cells:
        return set()
    max_col = max(col for _, col in cells)
    return _normalize((row, max_col - col) for row, col in cells)


def solve(grid):
    blue = _normalize(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    )
    red = _normalize(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    )

    flat = {value for row in grid for value in row}
    if 8 in flat:
        red = _rotate_clockwise(red)
    elif 9 in flat:
        red = _flip_horizontal(red)

    if 3 in flat:
        result = blue | red
    elif 4 in flat:
        result = blue & red
    elif 6 in flat:
        result = blue ^ red
    else:
        raise ValueError("missing operation control")

    result = _normalize(result)
    if not result:
        return [[0]]
    height = max(row for row, _ in result) + 1
    width = max(col for _, col in result) + 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in result:
        output[row][col] = 8
    return output
