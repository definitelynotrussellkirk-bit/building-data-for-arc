"""Visible-example solution for task 4ac45a758a2e."""
from __future__ import annotations


def _normalize(cells):
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return sorted((row - top, col - left) for row, col in cells)


def _rotate_clockwise(cells):
    cells = _normalize(cells)
    height = max(row for row, _col in cells) + 1
    return _normalize((col, height - 1 - row) for row, col in cells)


def _flip_horizontal(cells):
    cells = _normalize(cells)
    width = max(col for _row, col in cells) + 1
    return _normalize((row, width - 1 - col) for row, col in cells)


def solve(grid):
    """Copy the transformed magenta template in cyan at the orange anchor."""
    output = [list(row) for row in grid]
    template = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 6
    ]
    anchor = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 7
    )
    blue_count = sum(value == 1 for row in grid for value in row)
    red_count = sum(value == 2 for row in grid for value in row)

    shape = _normalize(template)
    for _ in range(blue_count - 1):
        shape = _rotate_clockwise(shape)
    if red_count == 2:
        shape = _flip_horizontal(shape)

    anchor_row, anchor_col = anchor
    for drow, dcol in _normalize(shape):
        output[anchor_row + drow][anchor_col + dcol] = 8
    return output
