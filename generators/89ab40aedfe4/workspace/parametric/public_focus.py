"""Exact visible-rule solver for public ARC evaluation task d59b0160.

A 3x3 legend occupies the top-left of an L-shaped color-3 border.  Every
four-connected external region that contains every non-background legend color
is erased to the color-7 background.  Other regions and the legend stay fixed.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

PUBLIC_TASK_ID = "d59b0160"
BACKGROUND = 7
BORDER = 3
KEY_INTERIOR = 3
KEY_SPAN = 4
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _validated_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or len(grid) < KEY_SPAN:
        raise ValueError("grid must contain the 4x4 top-left legend frame")
    if not isinstance(grid[0], list) or len(grid[0]) < KEY_SPAN:
        raise ValueError("grid must contain the 4x4 top-left legend frame")
    width = len(grid[0])
    copied: list[list[int]] = []
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be integer ARC colors 0..9")
        copied.append(list(row))
    if any(copied[KEY_INTERIOR][column] != BORDER for column in range(KEY_SPAN)):
        raise ValueError("legend bottom border must be color 3")
    if any(copied[row][KEY_INTERIOR] != BORDER for row in range(KEY_SPAN)):
        raise ValueError("legend right border must be color 3")
    return copied


def key_colors(grid: Any) -> frozenset[int]:
    """Return the set named by the 3x3 legend interior."""
    checked = _validated_grid(grid)
    colors = frozenset(
        checked[row][column]
        for row in range(KEY_INTERIOR)
        for column in range(KEY_INTERIOR)
        if checked[row][column] not in (BACKGROUND, BORDER)
    )
    if not colors:
        raise ValueError("legend must name at least one non-background color")
    return colors


def apply_rule(grid: Any) -> list[list[int]]:
    """Erase external four-connected regions containing every legend color."""
    checked = _validated_grid(grid)
    required = key_colors(checked)
    output = deepcopy(checked)
    height = len(checked)
    width = len(checked[0])
    seen: set[tuple[int, int]] = set()

    for start_row in range(height):
        for start_col in range(width):
            if start_row < KEY_SPAN and start_col < KEY_SPAN:
                continue
            if checked[start_row][start_col] == BACKGROUND or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            colors: set[int] = set()
            while stack:
                row, column = stack.pop()
                cells.append((row, column))
                colors.add(checked[row][column])
                for dr, dc in _CARDINAL:
                    rr, cc = row + dr, column + dc
                    if not (0 <= rr < height and 0 <= cc < width):
                        continue
                    if rr < KEY_SPAN and cc < KEY_SPAN:
                        continue
                    if checked[rr][cc] == BACKGROUND or (rr, cc) in seen:
                        continue
                    seen.add((rr, cc))
                    stack.append((rr, cc))
            if required.issubset(colors):
                for row, column in cells:
                    output[row][column] = BACKGROUND
    return output
