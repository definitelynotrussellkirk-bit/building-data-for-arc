"""Visible-example solution for task 5bba6e671cec."""
from __future__ import annotations

import math


def solve(grid):
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    fixed = {4, 7}
    colors = sorted({value for row in grid for value in row} - fixed)
    if len(colors) < 2:
        return [list(row) for row in grid]

    center_r = (len(grid) - 1) / 2.0
    center_c = (len(grid[0]) - 1) / 2.0

    def centroid_angle(color):
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        mean_r = sum(r for r, _ in cells) / len(cells)
        mean_c = sum(c for _, c in cells) / len(cells)
        # North is zero; angles increase clockwise.
        return math.atan2(mean_c - center_c, -(mean_r - center_r)) % (2.0 * math.pi)

    ordered = sorted(colors, key=centroid_angle)
    mapping = {
        color: ordered[(index - 1) % len(ordered)]
        for index, color in enumerate(ordered)
    }
    return [
        [value if value in fixed else mapping[value] for value in row]
        for row in grid
    ]
