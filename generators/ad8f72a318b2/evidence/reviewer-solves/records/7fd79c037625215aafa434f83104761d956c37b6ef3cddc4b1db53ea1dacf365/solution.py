"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations

from typing import Sequence


def _crop_nonzero(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return []
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [list(row[left : right + 1]) for row in grid[top : bottom + 1]]


def _rotate_cw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Select one panel, crop it, transform it, and recolor its support."""
    panel_index = sum(value == 1 for value in grid[0][:4]) - 1
    transform_code = grid[0][5]
    target_color = grid[0][7]

    panel_origins = ((2, 0), (2, 5), (7, 0), (7, 5))
    top, left = panel_origins[panel_index]
    panel = [row[left : left + 4] for row in grid[top : top + 4]]
    cropped = _crop_nonzero(panel)

    transforms = {
        1: lambda value: [list(row) for row in value],
        2: _rotate_cw,
        3: _rotate_180,
        4: _rotate_ccw,
        5: _flip_lr,
    }
    transformed = transforms[transform_code](cropped)
    return [
        [target_color if value != 0 else 0 for value in row]
        for row in transformed
    ]
