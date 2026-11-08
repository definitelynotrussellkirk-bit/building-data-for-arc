"""Visible-example solution for ARC task 26f313fdf812."""
from __future__ import annotations

from collections import deque


def _objects(grid: list[list[int]]) -> list[tuple[tuple[int, int], int]]:
    """Return ((top row, left column), cell count) for nonzero 4-components."""
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[tuple[tuple[int, int], int]] = []

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
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + dr
                    next_col = current_col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))

            top = min(cell[0] for cell in cells)
            left = min(cell[1] for cell in cells)
            objects.append(((top, left), len(cells)))

    objects.sort(key=lambda item: item[0])
    return objects


def solve(grid: list[list[int]]) -> list[list[int]]:
    sizes = [size for _position, size in _objects(grid)]
    return [
        [1 if row_size == col_size else (2 if row_size > col_size else 3)
         for col_size in sizes]
        for row_size in sizes
    ]
