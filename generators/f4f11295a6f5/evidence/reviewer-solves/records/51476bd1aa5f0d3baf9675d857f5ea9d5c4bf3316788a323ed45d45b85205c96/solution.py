"""Visible-example solution for f4f11295a6f5."""
from __future__ import annotations


def solve(grid):
    positions = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    ]
    if not positions:
        raise ValueError("expected at least one nonzero cell")
    top = min(row for row, _column in positions)
    bottom = max(row for row, _column in positions)
    left = min(column for _row, column in positions)
    right = max(column for _row, column in positions)
    pattern = [
        values[left : right + 1]
        for values in grid[top : bottom + 1]
    ]
    pattern_h = len(pattern)
    pattern_w = len(pattern[0])
    return [
        [
            (
                pattern[row % pattern_h][column % pattern_w]
                if pattern[row // pattern_h][column // pattern_w] != 0
                else 0
            )
            for column in range(pattern_w * pattern_w)
        ]
        for row in range(pattern_h * pattern_h)
    ]
