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
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            top = min(rr for rr, _ in cells)
            bottom = max(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            right = max(cc for _, cc in cells)
            crop = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
            for rr, cc in cells:
                crop[rr - top][cc - left] = color
            out.append((len(cells), top, bottom, left, right, crop))
    return out


def solve(grid):
    objects = sorted(_objects(grid), key=lambda item: (-item[0], item[1], item[2], item[3], item[4]))
    crops = [item[5] for item in objects]
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    result = [[0] * width for _ in range(height)]
    x = 0
    for crop in crops:
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                result[r][x + c] = value
        x += len(crop[0]) + 1
    return result
