"""Visible-example solution for the post-repair solve episode."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        nonzero = [(column, value) for column, value in enumerate(row) if value != 0]
        if len(nonzero) != 2 or nonzero[0][1] != nonzero[1][1]:
            continue
        left, color = nonzero[0]
        right = nonzero[1][0]
        for column in range(left, right + 1):
            out[row_index][column] = color
    return out
