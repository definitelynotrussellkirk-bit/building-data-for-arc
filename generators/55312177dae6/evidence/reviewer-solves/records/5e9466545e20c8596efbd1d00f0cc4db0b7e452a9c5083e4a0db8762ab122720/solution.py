"""Visible-example solution for ARC task 55312177dae6."""
from __future__ import annotations

from collections import Counter


def _norm(cells):
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _rotate(shape):
    shape = _norm(shape)
    height = max(r for r, _ in shape) + 1
    return _norm((c, height - 1 - r) for r, c in shape)


def _canonical_rotation(shape):
    forms = []
    current = _norm(shape)
    for _ in range(4):
        forms.append(current)
        current = _rotate(current)
    return min(forms)


def _components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    found = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        found.append(tuple(cells))
    return found


def solve(grid):
    canonical_shapes = [
        _canonical_rotation(component)
        for component in _components(grid)
    ]
    counts = Counter(canonical_shapes)
    target = next(shape for shape in canonical_shapes if counts[shape] >= 2)
    height = max(r for r, _ in target) + 1
    width = max(c for _, c in target) + 1
    output = [[0] * width for _ in range(height)]
    for r, c in target:
        output[r][c] = 8
    return output
