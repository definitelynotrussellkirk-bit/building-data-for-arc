"""Visible-example solution for ARC task 92f4d4eb0dbb."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    occupied_rows = [
        row_index
        for row_index, row in enumerate(grid)
        for value in row
        if value == 1
    ]
    if not occupied_rows:
        return deepcopy(grid)
    midpoint_twice = min(occupied_rows) + max(occupied_rows)
    return [
        [
            2 if value == 1 and 2 * row_index > midpoint_twice else value
            for value in row
        ]
        for row_index, row in enumerate(grid)
    ]
