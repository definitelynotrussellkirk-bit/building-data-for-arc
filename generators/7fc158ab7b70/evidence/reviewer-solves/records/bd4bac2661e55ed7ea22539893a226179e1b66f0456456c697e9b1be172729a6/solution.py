"""Visible-example solution for task 7fc158ab7b70."""
from __future__ import annotations

from typing import List

Grid = List[List[int]]


def solve(grid: Grid) -> Grid:
    scale = sum(value != 0 for row in grid for value in row)
    if scale <= 0:
        return [row[:] for row in grid]

    out: Grid = []
    for row in grid:
        expanded = [value for value in row for _ in range(scale)]
        out.extend([expanded[:] for _ in range(scale)])
    return out
