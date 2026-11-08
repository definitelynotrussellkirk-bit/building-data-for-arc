"""Visible-example solution for token-selected object transforms."""
from __future__ import annotations


def _crop_nonzero(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return []
    row_min = min(row for row, _ in cells)
    row_max = max(row for row, _ in cells)
    col_min = min(col for _, col in cells)
    col_max = max(col for _, col in cells)
    return [values[col_min : col_max + 1] for values in grid[row_min : row_max + 1]]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def solve(grid: list[list[int]]) -> list[list[int]]:
    command = grid[0][0]
    clean = [row[:] for row in grid]
    clean[0][0] = 0
    obj = _crop_nonzero(clean)

    if command == 1:
        return obj
    if command == 2:
        return _rotate_cw(obj)
    if command == 3:
        return _rotate_180(obj)
    if command in (4, 7):
        return _transpose(obj)
    if command == 5:
        return [row[::-1] for row in obj]
    if command == 6:
        return obj[::-1]
    if command == 8:
        return _rotate_180(_transpose(obj))
    raise ValueError(f"unsupported command token: {command!r}")
