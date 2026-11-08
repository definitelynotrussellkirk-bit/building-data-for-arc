"""Visible-example solution for the post-repair solve episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Return 1 exactly when every row is mirror-symmetric left-to-right."""
    return [[1 if all(row == row[::-1] for row in grid) else 7]]
