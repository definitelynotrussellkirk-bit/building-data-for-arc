"""Visible-example solution for the exposed reviewer-authored ARC task."""

from __future__ import annotations

from collections import deque
from typing import Iterable

Grid = list[list[int]]
Cell = tuple[int, int]


def _components(grid: Grid) -> list[tuple[int, set[Cell]]]:
    """Return 4-connected monochrome non-background objects."""
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


def _touches_border(cells: Iterable[Cell], height: int, width: int) -> bool:
    return any(
        row == 0 or row == height - 1 or col == 0 or col == width - 1
        for row, col in cells
    )


def _reflection_signature(cells: set[Cell]) -> tuple[bool, bool]:
    """Return (top/bottom reflection, left/right reflection) in the local box."""
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)

    local = {(row - min_row, col - min_col) for row, col in cells}
    local_height = max_row - min_row + 1
    local_width = max_col - min_col + 1

    top_bottom = {
        (local_height - 1 - row, col) for row, col in local
    } == local
    left_right = {
        (row, local_width - 1 - col) for row, col in local
    } == local
    return top_bottom, left_right


def solve(grid: Grid) -> Grid:
    """Recolor objects sharing the color-2 object's border/symmetry signature."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    objects = _components(grid)
    anchors = [cells for color, cells in objects if color == 2]
    if len(anchors) != 1:
        return [row[:] for row in grid]

    anchor = anchors[0]
    target_signature = (
        _touches_border(anchor, height, width),
        _reflection_signature(anchor),
    )

    output = [row[:] for row in grid]
    for color, cells in objects:
        if color == 2:
            continue
        signature = (
            _touches_border(cells, height, width),
            _reflection_signature(cells),
        )
        if signature == target_signature:
            for row, col in cells:
                output[row][col] = 8

    return output
