"""Visible-example solution for task 7017b91a367d."""
from __future__ import annotations


def solve(grid):
    """Overlay the three aligned 5x5 panels and encode occupancy count."""
    if len(grid) != 5 or any(len(row) != 17 for row in grid):
        raise ValueError("expected a 5x17 input containing three 5x5 panels")
    colors = (0, 2, 4, 8)
    return [
        [
            colors[sum(grid[r][c + 6 * panel] != 0 for panel in range(3))]
            for c in range(5)
        ]
        for r in range(5)
    ]
