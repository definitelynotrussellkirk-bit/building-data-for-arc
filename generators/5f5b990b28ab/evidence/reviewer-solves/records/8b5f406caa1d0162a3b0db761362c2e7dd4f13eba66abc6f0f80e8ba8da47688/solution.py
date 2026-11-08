"""Visible-example solution for task 5f5b990b28ab."""
from __future__ import annotations

from collections import deque

PALETTE = (2, 4, 6, 7, 3, 5, 9)


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    found: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for neighbour in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    cells.add(neighbour)
                    queue.append(neighbour)
        found.append(cells)
    return found


def _bbox_area(cells: set[tuple[int, int]]) -> int:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolour nonzero 4-connected objects by descending bbox area."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    objects = sorted(_components(grid), key=lambda cells: (-_bbox_area(cells), _bbox(cells)))
    for rank, cells in enumerate(objects):
        colour = PALETTE[rank]
        for row, col in cells:
            output[row][col] = colour
    return output
