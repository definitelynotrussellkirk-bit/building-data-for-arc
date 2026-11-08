from __future__ import annotations

from collections import deque
from typing import Iterable

Grid = list[list[int]]
Point = tuple[int, int]
_NEIGHBORS: tuple[Point, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _foreground_components(grid: Grid) -> Iterable[list[Point]]:
    """Yield 4-connected components of nonzero cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }

    while unseen:
        start = unseen.pop()
        component = [start]
        queue: deque[Point] = deque([start])
        while queue:
            row, col = queue.popleft()
            for d_row, d_col in _NEIGHBORS:
                neighbor = (row + d_row, col + d_col)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.append(neighbor)
                    queue.append(neighbor)
        yield component


def _hole_count(component: list[Point]) -> int:
    """Count 4-connected background regions enclosed by one component."""
    occupied = set(component)
    min_row = min(row for row, _ in component)
    max_row = max(row for row, _ in component)
    min_col = min(col for _, col in component)
    max_col = max(col for _, col in component)

    # One-cell padding guarantees that all exterior background is connected to
    # this local frame's boundary, even when the component fills its own bbox.
    top, bottom = min_row - 1, max_row + 1
    left, right = min_col - 1, max_col + 1
    background = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if (row, col) not in occupied
    }

    exterior_start = (top, left)
    queue: deque[Point] = deque([exterior_start])
    background.remove(exterior_start)
    while queue:
        row, col = queue.popleft()
        for d_row, d_col in _NEIGHBORS:
            neighbor = (row + d_row, col + d_col)
            if neighbor in background:
                background.remove(neighbor)
                queue.append(neighbor)

    holes = 0
    while background:
        holes += 1
        start = background.pop()
        queue.append(start)
        while queue:
            row, col = queue.popleft()
            for d_row, d_col in _NEIGHBORS:
                neighbor = (row + d_row, col + d_col)
                if neighbor in background:
                    background.remove(neighbor)
                    queue.append(neighbor)
    return holes


_HOLE_COLOR = {1: 1, 2: 2, 3: 3, 4: 7}


def solve(grid: Grid) -> Grid:
    """Recolor each shape using the visible hole-count color codebook."""
    result = [row[:] for row in grid]
    for component in _foreground_components(grid):
        holes = _hole_count(component)
        color = _HOLE_COLOR.get(holes, holes)
        for row, col in component:
            result[row][col] = color
    return result
