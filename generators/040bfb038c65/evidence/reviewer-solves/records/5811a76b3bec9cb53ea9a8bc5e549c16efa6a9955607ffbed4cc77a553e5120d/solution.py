"""Visible-example solve for task 040bfb038c65."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy


def _components(grid, color=4):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = current[0] + dr, current[1] + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(tuple(cells))
    return result


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _canonical_shape(cells):
    original = list(_normalize(cells))
    variants = []
    for reflected in (False, True):
        current = (
            [(row, -col) for row, col in original]
            if reflected
            else list(original)
        )
        for _ in range(4):
            variants.append(_normalize(current))
            current = [(col, -row) for row, col in current]
    return min(variants)


def solve(grid):
    objects = _components(grid)
    signatures = [_canonical_shape(cells) for cells in objects]
    counts = Counter(signatures)
    oddballs = [
        cells for cells, signature in zip(objects, signatures)
        if counts[signature] == 1
    ]
    if len(oddballs) != 1:
        return deepcopy(grid)
    output = deepcopy(grid)
    for row, col in oddballs[0]:
        output[row][col] = 8
    return output
