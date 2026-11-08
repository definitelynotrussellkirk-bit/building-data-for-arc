"""Visible-example solution for the exposed post-repair episode."""
from __future__ import annotations


def solve(grid):
    """Reflect a square grid across its anti-diagonal."""
    n = len(grid)
    return [
        [grid[n - 1 - c][n - 1 - r] for c in range(n)]
        for r in range(n)
    ]
