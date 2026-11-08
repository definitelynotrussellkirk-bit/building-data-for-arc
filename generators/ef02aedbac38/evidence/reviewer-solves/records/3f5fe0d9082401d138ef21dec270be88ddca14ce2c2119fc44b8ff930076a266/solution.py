"""Visible-example solution for ARC task ef02aedbac38."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replace each 5 by the input's other color and everything else by 0."""
    other_colors = {value for row in grid for value in row if value != 5}
    if len(other_colors) != 1:
        raise ValueError("expected exactly one input color besides 5")
    other = next(iter(other_colors))
    return [[other if value == 5 else 0 for value in row] for row in grid]
