"""Visible-example solution for the pairwise-union gallery task."""
from __future__ import annotations


def _objects(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            r1 = max(rr for rr, _ in cells)
            c1 = max(cc for _, cc in cells)
            crop = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
            for rr, cc in cells:
                crop[rr - r0][cc - c0] = 1
            out.append((c0, r0, crop))
    return sorted(out, key=lambda item: (item[0], item[1]))


def solve(grid):
    objects = _objects(grid)
    ph = max(len(crop) for _, _, crop in objects)
    pw = max(len(crop[0]) for _, _, crop in objects)
    shapes = []
    for _, _, crop in objects:
        padded = [[0] * pw for _ in range(ph)]
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                padded[r][c] = value
        shapes.append(padded)

    n = len(shapes)
    answer = [[0] * (n * pw + n - 1) for _ in range(n * ph + n - 1)]
    for i, first in enumerate(shapes):
        for j, second in enumerate(shapes):
            top = i * (ph + 1)
            left = j * (pw + 1)
            for r in range(ph):
                for c in range(pw):
                    if first[r][c] or second[r][c]:
                        answer[top + r][left + c] = 8
    return answer
