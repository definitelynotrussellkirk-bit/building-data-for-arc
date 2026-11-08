"""Visible-example solution for ba5056d6102e."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Intersect the occupancy masks above and below the solid separator row."""
    if not grid or not grid[0]:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separators = [
        index
        for index, row in enumerate(grid)
        if row[0] != 0 and all(value == row[0] for value in row)
    ]
    candidates = [
        index
        for index in separators
        if index == len(grid) - index - 1
    ]
    if len(candidates) != 1:
        raise ValueError("expected one centered solid nonzero separator row")

    separator = candidates[0]
    top = grid[:separator]
    bottom = grid[separator + 1 :]
    return [
        [8 if top_value != 0 and bottom_value != 0 else 0
         for top_value, bottom_value in zip(top_row, bottom_row)]
        for top_row, bottom_row in zip(top, bottom)
    ]
