"""Visible-example solution for ARC task 96d4a788da47."""
from __future__ import annotations


def solve(grid):
    """Move every nonzero 4-connected object left until its bbox touches col 0."""
    rows = [list(row) for row in grid]
    if not rows:
        return []
    height = len(rows)
    width = len(rows[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    unseen = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if rows[r][c] != 0
    }

    while unseen:
        start = min(unseen)
        color = rows[start[0]][start[1]]
        unseen.remove(start)
        stack = [start]
        cells = [start]
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                point = (nr, nc)
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and point in unseen
                    and rows[nr][nc] == color
                ):
                    unseen.remove(point)
                    stack.append(point)
                    cells.append(point)

        left = min(c for _, c in cells)
        for r, c in cells:
            output[r][c - left] = color

    return output
