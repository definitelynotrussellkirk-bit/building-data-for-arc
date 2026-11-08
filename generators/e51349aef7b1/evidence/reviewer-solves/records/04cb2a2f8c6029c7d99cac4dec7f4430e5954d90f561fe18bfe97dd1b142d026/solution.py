"""Visible-example solution for the three-panel transform analogy."""
from __future__ import annotations


def _crop(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not points:
        return []
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _binary(grid):
    return [[1 if value else 0 for value in row] for row in grid]


def _transform(grid, code):
    if code == 1:  # identity
        return [row[:] for row in grid]
    if code == 2:  # clockwise quarter turn
        return [list(row) for row in zip(*grid[::-1])]
    if code == 3:  # half turn
        return [list(reversed(row)) for row in reversed(grid)]
    if code == 4:  # main-diagonal transpose
        return [list(row) for row in zip(*grid)]
    if code == 5:  # left-right reflection
        return [list(reversed(row)) for row in grid]
    if code == 6:  # up-down reflection
        return [row[:] for row in reversed(grid)]
    raise ValueError(code)


def solve(grid):
    height = len(grid)
    dividers = [
        c for c in range(len(grid[0]))
        if all(grid[r][c] == 5 for r in range(height))
    ]
    d1, d2 = dividers
    a = [row[:d1] for row in grid]
    b = [row[d1 + 1 : d2] for row in grid]
    c = [row[d2 + 1 :] for row in grid]

    aa = _binary(_crop(a))
    bb = _binary(_crop(b))
    matches = [code for code in range(1, 7) if _transform(aa, code) == bb]
    code = matches[0] if matches else 1

    b_color = next(value for row in b for value in row if value not in (0, 5))
    transformed = _transform(_binary(_crop(c)), code)
    return [[b_color if value else 0 for value in row] for row in transformed]
