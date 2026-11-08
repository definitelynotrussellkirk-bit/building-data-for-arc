"""Visible-example solution: stable row-wise left compaction."""
from __future__ import annotations


def solve(grid):
    output = []
    for row in grid:
        nonzero = [value for value in row if value != 0]
        output.append(nonzero + [0] * (len(row) - len(nonzero)))
    return output
