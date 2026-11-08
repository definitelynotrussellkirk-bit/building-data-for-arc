"""Visible-example solution for ARC task d53534afb2ff.

Infer monochrome hollow rectangular frames. Every complete nonzero object
strictly inside one frame inherits that frame's color; objects outside remain.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable, Sequence

Cell = tuple[int, int]
Grid = list[list[int]]


def _components(grid: Sequence[Sequence[int]]) -> Iterable[tuple[int, set[Cell]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[Cell] = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: set[Cell] = set()
            while queue:
                current = queue.popleft()
                cells.add(current)
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = current[0] + drow, current[1] + dcol
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            yield color, cells


def _frame_box(cells: set[Cell]) -> tuple[int, int, int, int] | None:
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    if row1 - row0 < 2 or col1 - col0 < 2:
        return None
    perimeter = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if row in (row0, row1) or col in (col0, col1)
    }
    return (row0, row1, col0, col1) if cells == perimeter else None


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    output = [list(row) for row in grid]
    components = list(_components(grid))
    frames: list[tuple[int, tuple[int, int, int, int]]] = []
    for color, cells in components:
        box = _frame_box(cells)
        if box is not None:
            frames.append((color, box))

    for _color, cells in components:
        for frame_color, (row0, row1, col0, col1) in frames:
            if all(row0 < row < row1 and col0 < col < col1 for row, col in cells):
                for row, col in cells:
                    output[row][col] = frame_color
                break
    return output


transform = solve
apply = solve
