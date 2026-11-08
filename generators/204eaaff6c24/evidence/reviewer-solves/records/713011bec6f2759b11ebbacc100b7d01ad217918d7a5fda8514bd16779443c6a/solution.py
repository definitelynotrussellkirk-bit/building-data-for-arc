"""Visible-example solution for task 204eaaff6c24."""
from __future__ import annotations


def solve(grid):
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"expected exactly one nonzero color, found {sorted(colors)}")
    color = next(iter(colors))
    count = sum(value == color for row in grid for value in row)
    return [[color] * count]
