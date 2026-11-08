"""Visible-example solution for the post-repair ARC episode."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    """Cap maximal horizontal yellow (4) runs of exactly three with magenta (6)."""
    out = deepcopy(grid)
    if not grid:
        return out
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        col = 0
        while col < width:
            color = row[col]
            start = col
            while col < width and row[col] == color:
                col += 1
            length = col - start
            if color == 4 and length == 3:
                if start > 0 and row[start - 1] == 0:
                    out[row_index][start - 1] = 6
                if col < width and row[col] == 0:
                    out[row_index][col] = 6
    return out
