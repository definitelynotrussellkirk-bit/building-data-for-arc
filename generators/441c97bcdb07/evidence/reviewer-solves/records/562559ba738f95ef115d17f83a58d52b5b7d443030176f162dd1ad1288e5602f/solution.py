"""Visible-example ARC solver for task 441c97bcdb07.

The input contains three translated copies of one colored object occupying
three corners of an axis-aligned 2x2 arrangement.  Complete the missing
corner with a fourth identical copy.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

Grid = list[list[int]]
Cell = tuple[int, int]


def _components(grid: Grid) -> list[tuple[int, set[Cell]]]:
    """Return 4-connected non-background components as (color, cells)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[Cell] = set()
    result: list[tuple[int, set[Cell]]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            cells: set[Cell] = set()
            queue: deque[Cell] = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current_row, current_col = queue.popleft()
                cells.add((current_row, current_col))
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            result.append((color, cells))

    return result


def _origin_and_shape(cells: Iterable[Cell]) -> tuple[Cell, frozenset[Cell]]:
    materialized = set(cells)
    top = min(row for row, _ in materialized)
    left = min(col for _, col in materialized)
    shape = frozenset((row - top, col - left) for row, col in materialized)
    return (top, left), shape


def solve(grid: Grid) -> Grid:
    """Add the missing translated copy in the fourth rectangle corner."""
    output = [row[:] for row in grid]
    components = _components(grid)

    # The visible lesson has exactly three copies.  Grouping by color and
    # normalized shape keeps the inference local if unrelated noise appears.
    groups: dict[tuple[int, frozenset[Cell]], list[Cell]] = {}
    for color, cells in components:
        origin, shape = _origin_and_shape(cells)
        groups.setdefault((color, shape), []).append(origin)

    candidates = [
        (key, origins)
        for key, origins in groups.items()
        if len(origins) == 3
        and len({row for row, _ in origins}) == 2
        and len({col for _, col in origins}) == 2
    ]
    if len(candidates) != 1:
        return output

    (color, shape), origins = candidates[0]
    rows = {row for row, _ in origins}
    cols = {col for _, col in origins}
    occupied_origins = set(origins)
    missing_origins = [
        (row, col)
        for row in rows
        for col in cols
        if (row, col) not in occupied_origins
    ]
    if len(missing_origins) != 1:
        return output

    missing_row, missing_col = missing_origins[0]
    height = len(output)
    width = len(output[0]) if height else 0
    target_cells = [
        (missing_row + delta_row, missing_col + delta_col)
        for delta_row, delta_col in shape
    ]
    if any(
        not (0 <= row < height and 0 <= col < width) or output[row][col] != 0
        for row, col in target_cells
    ):
        return output

    for row, col in target_cells:
        output[row][col] = color
    return output
