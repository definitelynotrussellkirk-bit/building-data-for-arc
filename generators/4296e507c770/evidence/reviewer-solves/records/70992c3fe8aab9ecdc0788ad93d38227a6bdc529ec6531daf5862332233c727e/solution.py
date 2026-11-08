"""Visible-example solution for the generated transform-coded stamp puzzle."""
from __future__ import annotations


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return sorted((r - top, c - left) for r, c in cells)


def _transform(shape, color):
    shape = _normalize(shape)
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    transformed = []
    for r, c in shape:
        if color == 4:          # reflect left/right
            transformed.append((r, width - 1 - c))
        elif color == 5:        # reflect up/down
            transformed.append((height - 1 - r, c))
        elif color == 6:        # rotate clockwise
            transformed.append((c, height - 1 - r))
        else:                   # color 3: unchanged
            transformed.append((r, c))
    return _normalize(transformed)


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    template = _normalize(
        [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    )
    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (3, 4, 5, 6)
    ]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for anchor_r, anchor_c, color in markers:
        for dr, dc in _transform(template, color):
            output[anchor_r + dr][anchor_c + dc] = 8
    return output
