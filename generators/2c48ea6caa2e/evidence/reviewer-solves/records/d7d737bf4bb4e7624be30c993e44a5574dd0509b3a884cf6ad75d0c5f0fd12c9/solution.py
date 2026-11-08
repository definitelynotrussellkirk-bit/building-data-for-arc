"""Visible-example solution for task 2c48ea6caa2e."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    blues = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    if not blues:
        return [[0 for _col in range(width)] for _row in range(height)]

    top = min(row for row, _col in blues)
    bottom = max(row for row, _col in blues)
    left = min(col for _row, col in blues)
    right = max(col for _row, col in blues)
    row_counts = [sum(value == 1 for value in row) for row in grid]
    col_counts = [
        sum(grid[row][col] == 1 for row in range(height))
        for col in range(width)
    ]

    return [
        [
            1
            if grid[row][col] == 1
            else 2
            if (
                top <= row <= bottom
                and left <= col <= right
                and grid[row][col] == 0
                and (row_counts[row] >= 4 or col_counts[col] >= 4)
            )
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]
