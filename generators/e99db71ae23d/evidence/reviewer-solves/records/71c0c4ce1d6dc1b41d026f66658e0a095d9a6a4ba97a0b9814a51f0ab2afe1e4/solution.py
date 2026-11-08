"""Visible-example-derived solver for ARC task e99db71ae23d."""

from __future__ import annotations

from collections import deque


_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in _CARDINAL:
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == color
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            found.append(cells)
    return found


def _projection_shift(cells: list[tuple[int, int]], color: int) -> tuple[int, int]:
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)

    occupied = set(cells)
    missing = next(
        (row, col)
        for row in (min_row, max_row)
        for col in (min_col, max_col)
        if (row, col) not in occupied
    )
    toward_row = -1 if missing[0] == min_row else 1
    toward_col = -1 if missing[1] == min_col else 1
    if color == 5:
        return toward_row, toward_col
    return -toward_row, -toward_col


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    # Yellow first, then green, matching the collision priority in the examples.
    for source_color, projected_color in ((5, 4), (2, 3)):
        for cells in _components(grid, source_color):
            delta_row, delta_col = _projection_shift(cells, source_color)
            for row, col in cells:
                target_row = row + delta_row
                target_col = col + delta_col
                if 0 <= target_row < height and 0 <= target_col < width:
                    output[target_row][target_col] = projected_color

    return output
