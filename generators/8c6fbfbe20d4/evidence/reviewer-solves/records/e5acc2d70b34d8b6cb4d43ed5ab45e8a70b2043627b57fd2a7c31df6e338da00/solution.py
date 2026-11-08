"""Visible-example solution for task 8c6fbfbe20d4."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Use the first two rows as ordered sparse source/target color lists."""
    sources = [value for value in grid[0] if value != 0]
    targets = [value for value in grid[1] if value != 0]
    mapping = dict(zip(sources, targets))
    return [
        [mapping.get(value, value) for value in row]
        for row in grid[2:]
    ]
