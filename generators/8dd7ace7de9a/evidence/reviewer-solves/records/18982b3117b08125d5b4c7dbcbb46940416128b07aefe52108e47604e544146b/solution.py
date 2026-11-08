"""Visible-example solution for the periodic-noise task."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replace color-6 corruption by the smallest consistent repeating tile."""
    h = len(grid)
    w = len(grid[0])
    for row_period in range(1, h // 2 + 1):
        for col_period in range(1, w // 2 + 1):
            tile: dict[tuple[int, int], int] = {}
            consistent = True
            for r, row in enumerate(grid):
                for c, value in enumerate(row):
                    if value == 6:
                        continue
                    residue = (r % row_period, c % col_period)
                    previous = tile.get(residue)
                    if previous is None:
                        tile[residue] = value
                    elif previous != value:
                        consistent = False
                        break
                if not consistent:
                    break
            if consistent and len(tile) == row_period * col_period:
                return [
                    [tile[(r % row_period, c % col_period)] for c in range(w)]
                    for r in range(h)
                ]
    return [[0 for _ in range(w)] for _ in range(h)]
