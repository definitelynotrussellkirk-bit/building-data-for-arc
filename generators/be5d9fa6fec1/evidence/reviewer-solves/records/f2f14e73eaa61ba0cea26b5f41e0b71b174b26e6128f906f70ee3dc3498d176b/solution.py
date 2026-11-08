"""Visible-example solution for be5d9fa6fec1."""
from __future__ import annotations


def solve(grid):
    """Recolor nonzero cells in zero-based row-pattern groups 0, 3, 6, ... ."""
    if not grid:
        return []
    output = [list(row) for row in grid]
    group_index = 0
    previous = tuple(grid[0])
    for row_index, row in enumerate(grid):
        current = tuple(row)
        if row_index and current != previous:
            group_index += 1
        if group_index % 3 == 0:
            output[row_index] = [2 if value != 0 else 0 for value in row]
        previous = current
    return output
