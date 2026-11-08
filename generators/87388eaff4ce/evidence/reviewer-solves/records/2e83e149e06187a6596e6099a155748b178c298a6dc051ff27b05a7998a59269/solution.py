"""Visible-example solution for the post-repair episode."""
from __future__ import annotations


def _objects(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            for rr, cc in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            crop = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
            for rr, cc in cells:
                crop[rr - r0][cc - c0] = color
            objects.append((r1 - r0 + 1, color, crop))
    return objects


def solve(grid):
    objects = sorted(_objects(grid), key=lambda item: (-item[0], item[1]))
    out_h = sum(len(crop) for _, _, crop in objects) + max(0, len(objects) - 1)
    out_w = max(len(crop[0]) for _, _, crop in objects)
    out = [[0] * out_w for _ in range(out_h)]
    top = 0
    for _, _, crop in objects:
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value:
                    out[top + r][c] = value
        top += len(crop) + 1
    return out
