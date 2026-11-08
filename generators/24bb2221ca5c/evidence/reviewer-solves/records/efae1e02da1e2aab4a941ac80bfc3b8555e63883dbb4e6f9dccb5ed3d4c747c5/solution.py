"""Visible-example solution for ARC task 24bb2221ca5c."""
from __future__ import annotations

from collections import deque


_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[tuple[int, set[tuple[int, int]]]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells: set[tuple[int, int]] = set()
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current = queue.popleft()
                cells.add(current)
                cr, cc = current
                for dr, dc in _DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append((color, cells))
    return found


def _enclosed_bbox_zeros(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    row0, row1 = min(rows), max(rows)
    col0, col1 = min(cols), max(cols)

    zeros = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if (row, col) not in cells
    }
    exterior = {
        (row, col)
        for row, col in zeros
        if row in (row0, row1) or col in (col0, col1)
    }
    queue = deque(exterior)
    while queue:
        row, col = queue.popleft()
        for dr, dc in _DIR4:
            neighbor = (row + dr, col + dc)
            if neighbor in zeros and neighbor not in exterior:
                exterior.add(neighbor)
                queue.append(neighbor)
    return zeros - exterior


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill each component's enclosed zero regions with its own color."""
    output = [row[:] for row in grid]
    for color, cells in _components(grid):
        for row, col in _enclosed_bbox_zeros(cells):
            output[row][col] = color
    return output
