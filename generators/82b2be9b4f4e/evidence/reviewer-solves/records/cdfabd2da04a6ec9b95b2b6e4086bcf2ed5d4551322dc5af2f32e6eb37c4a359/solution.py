"""Visible-example solution for task 82b2be9b4f4e."""
from __future__ import annotations


def solve(grid):
    work = [row[:] for row in grid]
    h, w = len(work), len(work[0])
    key = work[h - 1][0]
    work[h - 1][0] = 0

    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if work[r][c] != key or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and work[nr][nc] == key
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objects.append(cells)

    winner = max(objects, key=len)
    r0 = min(r for r, _ in winner)
    r1 = max(r for r, _ in winner)
    c0 = min(c for _, c in winner)
    c1 = max(c for _, c in winner)
    crop = [row[c0 : c1 + 1] for row in work[r0 : r1 + 1]]
    return [
        [value for value in row for _ in range(2)]
        for row in crop
        for _ in range(2)
    ]
