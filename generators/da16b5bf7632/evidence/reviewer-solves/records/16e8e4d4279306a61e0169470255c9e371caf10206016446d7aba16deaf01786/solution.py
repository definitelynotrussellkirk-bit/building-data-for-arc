"""Blind solution for task da16b5bf7632.

Extract every non-background 4-connected component, rank components by the
number of enclosed background regions (holes), preserving reading order for
ties, then crop and concatenate them horizontally with one zero column.
"""
from collections import deque


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
            cells = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and (nx, ny) not in seen
                        and grid[nx][ny] == color
                    ):
                        seen.add((nx, ny))
                        q.append((nx, ny))
            out.append((color, cells))
    return out


def _crop_and_holes(color, cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    shape = [[0] * w for _ in range(h)]
    occupied = set()
    for r, c in cells:
        rr, cc = r - r0, c - c0
        shape[rr][cc] = color
        occupied.add((rr, cc))

    # Count empty 4-connected regions that cannot reach the crop boundary.
    empty_seen = set()
    holes = 0
    for r in range(h):
        for c in range(w):
            if (r, c) in occupied or (r, c) in empty_seen:
                continue
            q = deque([(r, c)])
            empty_seen.add((r, c))
            touches_boundary = False
            while q:
                x, y = q.popleft()
                if x in (0, h - 1) or y in (0, w - 1):
                    touches_boundary = True
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < h
                        and 0 <= ny < w
                        and (nx, ny) not in occupied
                        and (nx, ny) not in empty_seen
                    ):
                        empty_seen.add((nx, ny))
                        q.append((nx, ny))
            if not touches_boundary:
                holes += 1
    return shape, holes, r0, c0


def solve(grid):
    ranked = []
    for color, cells in _components(grid):
        shape, holes, r0, c0 = _crop_and_holes(color, cells)
        ranked.append((-holes, r0, c0, shape))
    ranked.sort(key=lambda item: item[:3])

    shapes = [item[3] for item in ranked]
    out_h = max(len(shape) for shape in shapes)
    out_w = sum(len(shape[0]) for shape in shapes) + len(shapes) - 1
    out = [[0] * out_w for _ in range(out_h)]

    offset = 0
    for i, shape in enumerate(shapes):
        for r, row in enumerate(shape):
            out[r][offset : offset + len(row)] = row
        offset += len(shape[0])
        if i + 1 < len(shapes):
            offset += 1
    return out
