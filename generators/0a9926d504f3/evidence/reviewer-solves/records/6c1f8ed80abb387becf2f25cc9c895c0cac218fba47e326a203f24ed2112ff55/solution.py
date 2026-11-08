"""Visible-example solution for the prepared 0a9926d504f3 episode."""
from __future__ import annotations


def solve(grid):
    h = len(grid)
    w = len(grid[0])
    cells = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    ]
    center = next((p for p in cells if grid[p[0]][p[1]] == 2), None)
    others = [p for p in cells if grid[p[0]][p[1]] != 2]
    if center is None or not others:
        raise ValueError("expected a color-2 center and non-center markers")

    cr, cc = center
    top = min(others, key=lambda p: p[0])
    bottom = max(others, key=lambda p: p[0])
    left = min(others, key=lambda p: p[1])
    right = max(others, key=lambda p: p[1])

    tr = top[0]
    br = bottom[0]
    lc = left[1]
    rc = right[1]
    top_color = grid[top[0]][top[1]]
    bottom_color = grid[bottom[0]][bottom[1]]
    left_color = grid[left[0]][left[1]]
    right_color = grid[right[0]][right[1]]

    out = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if r == tr and lc <= c <= rc:
                out[r][c] = top_color
            elif r == br and lc <= c <= rc:
                out[r][c] = bottom_color
            elif c == lc and tr <= r <= br:
                out[r][c] = left_color
            elif c == rc and tr <= r <= br:
                out[r][c] = right_color
            elif r == cr and c == cc:
                out[r][c] = 2
            elif r == cr and lc < c < rc:
                out[r][c] = 5
            elif c == cc and tr < r < br:
                out[r][c] = 5
    return out
