"""Visible-example solution for bc932ac8117a."""
from collections import deque
from copy import deepcopy

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while q:
                cr, cc = q.popleft()
                cells.add((cr, cc))
                for dr, dc in DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            rows = [x for x, _ in cells]
            cols = [y for _, y in cells]
            out.append({"cells": cells,
                        "bbox": (min(rows), min(cols), max(rows), max(cols))})
    return out


def _holes(obj):
    r0, c0, r1, c1 = obj["bbox"]
    h, w = r1 - r0 + 1, c1 - c0 + 1
    occupied = {(r - r0, c - c0) for r, c in obj["cells"]}
    seen = set()
    enclosed = []
    for r in range(h):
        for c in range(w):
            if (r, c) in occupied or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            region = set()
            touches_edge = False
            while q:
                cr, cc = q.popleft()
                region.add((cr, cc))
                if cr in (0, h - 1) or cc in (0, w - 1):
                    touches_edge = True
                for dr, dc in DIR4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in occupied and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            if not touches_edge:
                enclosed.append(region)
    return enclosed


def solve(grid):
    objects = _components(grid)
    with_holes = [(obj, _holes(obj)) for obj in objects]
    hollow, holes = next((obj, holes) for obj, holes in with_holes if holes)
    hr0, hc0, hr1, hc1 = hollow["bbox"]
    shape = (hr1 - hr0 + 1, hc1 - hc0 + 1)
    solid = next(
        obj for obj, obj_holes in with_holes
        if not obj_holes and
        (obj["bbox"][2] - obj["bbox"][0] + 1,
         obj["bbox"][3] - obj["bbox"][1] + 1) == shape
    )
    sr0, sc0, _, _ = solid["bbox"]
    result = deepcopy(grid)
    for region in holes:
        for r, c in region:
            result[sr0 + r][sc0 + c] = 0
    return result
