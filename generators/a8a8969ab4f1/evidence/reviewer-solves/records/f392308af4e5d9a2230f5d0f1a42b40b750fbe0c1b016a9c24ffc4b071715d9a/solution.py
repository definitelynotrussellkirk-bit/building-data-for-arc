"""Visible-example solution for the generated row-key task."""
from __future__ import annotations


def solve(grid):
    output = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        key = row[0]
        if key == 0:
            continue
        for column in range(1, len(row)):
            if row[column] == 8:
                output[row_index][column] = key
    return output
