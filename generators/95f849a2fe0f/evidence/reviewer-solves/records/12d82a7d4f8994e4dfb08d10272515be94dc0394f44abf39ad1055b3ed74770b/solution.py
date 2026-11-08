"""Visible-example solution for reviewer-authored task 95f849a2fe0f."""
from __future__ import annotations


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def solve(grid):
    """Normalize the 2- and 3-objects, then render their XOR in cyan."""
    shapes = []
    for color in (2, 3):
        cells = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        }
        if not cells:
            raise ValueError(f"missing color {color} object")
        shapes.append(_normalize(cells))

    xor = shapes[0] ^ shapes[1]
    if not xor:
        return [[0]]
    height = max(r for r, _ in xor) + 1
    width = max(c for _, c in xor) + 1
    return [
        [8 if (r, c) in xor else 0 for c in range(width)]
        for r in range(height)
    ]
