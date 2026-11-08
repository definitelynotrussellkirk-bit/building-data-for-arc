from __future__ import annotations


def _normalized_mask(grid, color):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    if not cells:
        raise ValueError(f"missing color {color}")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def solve(grid):
    red = _normalized_mask(grid, 2)
    green = _normalized_mask(grid, 3)
    xor = red ^ green
    if not xor:
        return [[0]]

    r0 = min(r for r, _ in xor)
    c0 = min(c for _, c in xor)
    r1 = max(r for r, _ in xor)
    c1 = max(c for _, c in xor)
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in xor:
        out[r - r0][c - c0] = 8
    return out
