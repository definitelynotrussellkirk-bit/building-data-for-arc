"""Visible-example solution for the prepared reviewer puzzle."""
from collections import defaultdict


def _sign(value):
    return (value > 0) - (value < 0)


def solve(grid):
    """Replace each twice-occurring nonzero color by its inclusive cyan span."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    points = defaultdict(list)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                points[color].append((row, col))

    for cells in points.values():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = sorted(cells)
        dr = _sign(r2 - r1)
        dc = _sign(c2 - c1)
        steps = max(abs(r2 - r1), abs(c2 - c1))
        for index in range(steps + 1):
            out[r1 + index * dr][c1 + index * dc] = 8
    return out
