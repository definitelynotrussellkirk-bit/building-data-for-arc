"""Select the unique exact crop among multicolor, eight-connected objects."""
from __future__ import annotations
from collections import Counter


def _crops(grid: list[list[int]], *, diagonal: bool = True):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    patterns = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if not (dr or dc):
                        continue
                    if not diagonal and abs(dr) + abs(dc) != 1:
                        continue
                    neighbor = (r + dr, c + dc)
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        component.add(neighbor)
                        stack.append(neighbor)
        top = min(r for r, c in component)
        bottom = max(r for r, c in component)
        left = min(c for r, c in component)
        right = max(c for r, c in component)
        patterns.append(tuple(tuple(grid[r][left:right + 1]) for r in range(top, bottom + 1)))
    return patterns


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        raise ValueError('Expected a nonempty grid')
    if len({len(row) for row in grid}) != 1:
        raise ValueError('Expected a rectangular grid')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('Expected integer colors from 0 through 9')
    patterns = _crops(grid)
    counts = Counter(patterns)
    unique = [pattern for pattern, count in counts.items() if count == 1]
    if len(unique) != 1:
        raise ValueError(f'Expected exactly one unique crop, found {len(unique)}')
    return [list(row) for row in unique[0]]
