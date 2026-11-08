"""Visible-example solution for task 0c5e8548d3be."""
from __future__ import annotations


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _rotate(shape):
    shape = _normalize(shape)
    if not shape:
        return ()
    height = max(r for r, _ in shape) + 1
    return _normalize((c, height - 1 - r) for r, c in shape)


def _rotation_key(shape):
    forms = []
    current = _normalize(shape)
    for _ in range(4):
        forms.append(current)
        current = _rotate(current)
    return min(forms)


def solve(grid):
    starts = (0, 6, 12, 18)
    keys = []
    for start in starts:
        shape = [
            (row, offset)
            for row in range(len(grid))
            for offset in range(5)
            if grid[row][start + offset] != 0
        ]
        keys.append(_rotation_key(shape))
    return [[8 if left == right else 0 for right in keys] for left in keys]
