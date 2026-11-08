"""Visible-example solution for e07bbcbe6ba4."""
from __future__ import annotations


def solve(grid):
    """Fill the framed interior with alternating square rings around its marker."""
    result = [row[:] for row in grid]
    threes = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    if not threes:
        return result

    top = min(r for r, _ in threes)
    bottom = max(r for r, _ in threes)
    left = min(c for _, c in threes)
    right = max(c for _, c in threes)
    markers = [
        (r, c)
        for r, c in threes
        if top < r < bottom and left < c < right
    ]
    if len(markers) != 1:
        raise ValueError(f"expected one interior marker, found {len(markers)}")
    marker_r, marker_c = markers[0]

    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if grid[r][c] != 0:
                continue
            distance = max(abs(r - marker_r), abs(c - marker_c))
            result[r][c] = 2 if distance % 2 == 0 else 4
    return result
