"""Blind ARC solve for task 372fcf6aa6ad.

Only the visible challenge examples were used to derive this solution.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

Grid = list[list[int]]


def _components(grid: Grid) -> list[tuple[int, Grid]]:
    """Return (painted-cell-count, cropped-object-grid) components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    found: list[tuple[int, Grid]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            min_row = min(r for r, _ in cells)
            max_row = max(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            max_col = max(c for _, c in cells)
            cell_set = set(cells)
            cropped = [
                [
                    color if (source_row, source_col) in cell_set else 0
                    for source_col in range(min_col, max_col + 1)
                ]
                for source_row in range(min_row, max_row + 1)
            ]
            found.append((len(cells), cropped))

    return found


def _rotate_clockwise(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _color(grid: Grid) -> int:
    return next(value for row in grid for value in row if value != 0)


def solve(grid: Grid) -> Grid:
    """Rotate and pack objects in ascending size order."""
    objects = _components(grid)
    objects.sort(key=lambda item: (item[0], -_color(item[1])))
    rotated = [_rotate_clockwise(obj) for _, obj in objects]

    output_height = max(len(obj) for obj in rotated)
    output_width = sum(len(obj[0]) for obj in rotated) + max(0, len(rotated) - 1)
    output = [[0] * output_width for _ in range(output_height)]

    cursor = 0
    for obj in rotated:
        top = (output_height - len(obj)) // 2
        for row, values in enumerate(obj):
            output[top + row][cursor : cursor + len(values)] = values
        cursor += len(obj[0]) + 1

    return output
