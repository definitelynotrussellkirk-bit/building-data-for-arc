"""Visible-example solution for ARC task 424c822d69f3."""

from __future__ import annotations

from collections import deque
from typing import Iterable

Grid = list[list[int]]


def _five_components(grid: Grid) -> Iterable[list[tuple[int, int]]]:
    """Yield the 4-connected components made of color 5."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()

    for row in range(height):
        for col in range(width):
            start = (row, col)
            if grid[row][col] != 5 or start in seen:
                continue

            component: list[tuple[int, int]] = []
            queue = deque([start])
            seen.add(start)
            while queue:
                current_row, current_col = queue.popleft()
                component.append((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    next_cell = (next_row, next_col)
                    if next_cell in seen or grid[next_row][next_col] != 5:
                        continue
                    seen.add(next_cell)
                    queue.append(next_cell)

            yield component


def solve(grid: Grid) -> Grid:
    """Recolor each 5-object with the horizontally nearest top-row marker."""
    if not grid:
        return []

    output = [row[:] for row in grid]
    markers = [
        (column, color)
        for column, color in enumerate(grid[0])
        if color not in (0, 5)
    ]
    if not markers:
        return output

    for component in _five_components(grid):
        min_col = min(column for _, column in component)
        max_col = max(column for _, column in component)
        # For an even-width box, use its left middle column. This is the
        # integer midpoint visibly consistent with the examples.
        center_col = (min_col + max_col) // 2
        _, replacement = min(
            markers,
            key=lambda marker: (abs(marker[0] - center_col), marker[0]),
        )
        for row, column in component:
            output[row][column] = replacement

    return output
