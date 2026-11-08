"""Code-aware directed rays; mapping selected by the visible-only mapping probe."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError('grid must be a nonempty list of nonempty rows')
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError('grid must be rectangular')
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError('cells must be integer colors from 0 through 9')
    direction = {1: (-1, 0), 2: (1, 0), 3: (0, -1), 4: (0, 1)}
    output = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            delta = direction.get(grid[r][c])
            if delta is None:
                continue
            dr, dc = delta
            sr, sc = r-dr, c-dc
            if not (0 <= sr < h and 0 <= sc < w):
                continue
            color = grid[sr][sc]
            if color < 5:
                continue
            rr, cc = sr, sc
            while 0 <= rr < h and 0 <= cc < w:
                output[rr][cc] = color
                rr += dr
                cc += dc
    return output
