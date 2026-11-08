"""Visible-example solution for 7ce16af847d6."""
from __future__ import annotations


def solve(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError("expected a rectangular grid")

    out = [row[:] for row in grid]
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    while unseen:
        start = unseen.pop()
        cells = {start}
        todo = [start]
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    todo.append(point)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        height = max(rows) - min(rows) + 1
        width = max(cols) - min(cols) + 1
        if len(cells) == 9 and height == 3 and width == 3:
            for r, c in cells:
                out[r][c] = 3
    return out
