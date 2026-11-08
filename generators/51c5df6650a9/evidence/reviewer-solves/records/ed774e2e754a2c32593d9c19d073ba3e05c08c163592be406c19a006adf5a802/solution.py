"""Visible-example solution for Legend-Ordered Pack."""
from __future__ import annotations

from collections import deque


def solve(grid):
    h, w = len(grid), len(grid[0])
    colors = []
    seen_colors = set()
    for value in grid[0]:
        if value != 0 and value not in seen_colors:
            seen_colors.add(value)
            colors.append(value)

    def component(color):
        starts = [
            (r, c)
            for r in range(1, h)
            for c in range(w)
            if grid[r][c] == color
        ]
        if not starts:
            return []
        start = min(starts)
        cells = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if (
                    1 <= point[0] < h
                    and 0 <= point[1] < w
                    and point not in cells
                    and grid[point[0]][point[1]] == color
                ):
                    cells.add(point)
                    queue.append(point)
        return cells

    out = [[0] * w for _ in range(h)]
    left = 0
    for color in colors:
        cells = component(color)
        if not cells:
            continue
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        for r, c in cells:
            rr = 1 + (r - r0)
            cc = left + (c - c0)
            if rr < h and cc < w:
                out[rr][cc] = color
        left += (c1 - c0 + 1) + 1
    return out
