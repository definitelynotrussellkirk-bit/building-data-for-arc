"""Visible-example solution for the reviewer puzzle."""
from copy import deepcopy


def solve(grid):
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        endpoints = [c for c, value in enumerate(row) if value == 5]
        if len(endpoints) != 2:
            continue
        left, right = endpoints
        if right <= left + 1:
            continue
        if all(row[c] == 0 for c in range(left + 1, right)):
            for c in range(left + 1, right):
                out[r][c] = 3
    return out
