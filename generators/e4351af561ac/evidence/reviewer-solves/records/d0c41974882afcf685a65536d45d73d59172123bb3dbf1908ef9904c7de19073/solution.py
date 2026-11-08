"""Visible-example solution for e4351af561ac."""
from __future__ import annotations

from collections import deque

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append((color, tuple(cells)))
    return result


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _rotate(shape):
    return _normalize((col, -row) for row, col in shape)


def _rotations(cells):
    shape = _normalize(cells)
    result = set()
    for _ in range(4):
        result.add(shape)
        shape = _rotate(shape)
    return result


def solve(grid):
    """Keep green components rotationally congruent to the blue template."""
    components = _components(grid)
    templates = [cells for color, cells in components if color == 1]
    if len(templates) != 1:
        raise ValueError("expected exactly one blue template component")

    accepted = _rotations(templates[0])
    output = [[0 for _ in row] for row in grid]
    for color, cells in components:
        if color == 3 and _normalize(cells) in accepted:
            for row, col in cells:
                output[row][col] = 8
    return output
