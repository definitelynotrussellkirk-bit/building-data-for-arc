"""Visible-example solution for task 0f7d80015d9d."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    gray = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    ]
    if not gray:
        raise ValueError("missing gray rectangle")

    bottom = max(r for r, _ in gray)
    left = min(c for _, c in gray)
    right = max(c for _, c in gray)
    midpoint = (left + right) // 2

    red = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    cyan = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    )

    out[red[0]][red[1]] = 7
    out[cyan[0]][cyan[1]] = 2
    destination_col = right + 1 if red[1] < midpoint else left - 1
    if not 0 <= destination_col < len(grid[0]):
        raise ValueError("derived cyan destination is out of bounds")
    out[bottom][destination_col] = 8
    return out
