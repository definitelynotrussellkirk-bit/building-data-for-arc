"""Visible-example solution for the prepared ARC episode."""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Iterable


Cell = tuple[int, int]
Grid = list[list[int]]


def _components(grid: Grid, color: int) -> list[list[Cell]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    unseen = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == color
    }
    result: list[list[Cell]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue: deque[Cell] = deque([start])
        cells: list[Cell] = []
        while queue:
            row, column = queue.popleft()
            cells.append((row, column))
            for next_cell in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if next_cell in unseen:
                    unseen.remove(next_cell)
                    queue.append(next_cell)
        result.append(sorted(cells))
    return result


def _bbox(cells: Iterable[Cell]) -> tuple[int, int, int, int]:
    cells = list(cells)
    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    return min(rows), min(columns), max(rows), max(columns)


def solve(grid: Grid) -> Grid:
    """Stamp the largest magenta component's mask into the green rectangle."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    magenta = _components(grid, 6)
    green = _components(grid, 3)
    if not magenta or not green:
        raise ValueError("expected magenta template and green target")

    template = max(magenta, key=lambda cells: (len(cells), tuple(cells)))
    template_top, template_left, template_bottom, template_right = _bbox(template)
    template_height = template_bottom - template_top + 1
    template_width = template_right - template_left + 1

    matching_targets = []
    for component in green:
        top, left, bottom, right = _bbox(component)
        if bottom - top + 1 == template_height and right - left + 1 == template_width:
            matching_targets.append(component)
    if len(matching_targets) != 1:
        raise ValueError("expected one green component matching the template bounds")

    target = matching_targets[0]
    target_top, target_left, _, _ = _bbox(target)
    output = deepcopy(grid)
    for row, column in target:
        output[row][column] = 0
    for row, column in template:
        output[
            target_top + row - template_top
        ][
            target_left + column - template_left
        ] = 8
    return output
