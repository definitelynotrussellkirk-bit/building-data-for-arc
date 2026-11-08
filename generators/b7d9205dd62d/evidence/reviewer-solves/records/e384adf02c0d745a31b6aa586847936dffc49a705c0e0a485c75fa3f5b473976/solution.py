"""Infer rectangles from same-colour diagonal corner pairs."""
from collections import defaultdict


def solve(grid):
    result = [list(row) for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions[color].append((r, c))
    for color, cells in positions.items():
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        if r0 == r1 or c0 == c1:
            continue
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                result[r][c] = color
    return result
