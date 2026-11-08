"""Visible-example solution for task 26dbe76edccd."""

from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend each colored non-gray seed rightward until gray or the border."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color in (0, 5):
                continue
            for x in range(c + 1, len(row)):
                if row[x] == 5:
                    break
                if row[x] == 0:
                    out[r][x] = color
    return out
