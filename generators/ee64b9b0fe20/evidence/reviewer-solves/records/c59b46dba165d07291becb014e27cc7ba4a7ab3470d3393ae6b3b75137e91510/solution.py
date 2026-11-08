"""Visible-example solve attempt; no generator/reference imports.

Prior authoring exposure is disclosed in SOLVE_NOTES.md. The frame-removal branch
is not determined by these three demonstrations, which contain no enclosing frame.
"""
from __future__ import annotations
from collections import Counter


def _objects(grid: list[list[int]], background: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[list[tuple[int, int]]] = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == background or (r, c) in seen:
                continue
            color = grid[r][c]
            pending = [(r, c)]
            seen.add((r, c))
            cells = []
            while pending:
                y, x = pending.pop()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = y + dy, x + dx
                    ny, nx = neighbor
                    if (0 <= ny < height and 0 <= nx < width and
                            neighbor not in seen and grid[ny][nx] == color):
                        seen.add(neighbor)
                        pending.append(neighbor)
            objects.append(cells)
    return objects


def _bounds(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return min(r for r, c in cells), min(c for r, c in cells), max(r for r, c in cells), max(c for r, c in cells)


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError('expected a nonempty grid')
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError('expected a rectangular grid')
    if any(type(color) is not int or not 0 <= color <= 9 for row in grid for color in row):
        raise ValueError('expected colors 0..9')
    background = Counter(color for row in grid for color in row).most_common(1)[0][0]
    components = [cells for cells in _objects(grid, background)
                  if _bounds(cells) != (0, 0, height - 1, width - 1)]
    output = [[background] * width for _ in range(height)]
    left = 0
    for cells in sorted(components, key=len):
        top, start, bottom, end = _bounds(cells)
        if left + end - start + 1 > width:
            raise ValueError('packed objects exceed output width')
        for r, c in cells:
            output[height - 1 - bottom + r][left + c - start] = grid[r][c]
        left += end - start + 1
    return output
