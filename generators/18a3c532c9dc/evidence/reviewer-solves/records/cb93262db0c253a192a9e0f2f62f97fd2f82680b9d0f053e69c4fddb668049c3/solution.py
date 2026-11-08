"""Visible-example solution for the exposed post-repair puzzle."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Overlay four equal quadrants with TR > BL > BR > TL priority."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    if height % 2 or width % 2 or any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid with even dimensions")

    half_h = height // 2
    half_w = width // 2
    output = [[0 for _ in range(half_w)] for _ in range(half_h)]
    for row in range(half_h):
        for col in range(half_w):
            tl = grid[row][col]
            tr = grid[row][col + half_w]
            bl = grid[row + half_h][col]
            br = grid[row + half_h][col + half_w]
            value = tl
            if br != 0:
                value = br
            if bl != 0:
                value = bl
            if tr != 0:
                value = tr
            output[row][col] = value
    return output
