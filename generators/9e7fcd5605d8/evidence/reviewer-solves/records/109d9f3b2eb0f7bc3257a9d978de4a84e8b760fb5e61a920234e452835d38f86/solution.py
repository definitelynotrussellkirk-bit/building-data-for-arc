"""Visible-example solution for task 9e7fcd5605d8."""
from collections import deque

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            cells = []
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield cells


def _encloses_hole(cells):
    occupied = set(cells)
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)

    background = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if (r, c) not in occupied
    }
    seen = set()
    for start in background:
        if start in seen:
            continue
        region = {start}
        queue = deque([start])
        seen.add(start)
        touches_boundary = False
        while queue:
            r, c = queue.popleft()
            if r in (r0, r1) or c in (c0, c1):
                touches_boundary = True
            for dr, dc in DIRS:
                nxt = (r + dr, c + dc)
                if nxt in background and nxt not in seen:
                    seen.add(nxt)
                    region.add(nxt)
                    queue.append(nxt)
        if not touches_boundary:
            return True
    return False


def solve(grid):
    if not grid or not grid[0]:
        return grid
    out = [[0 for _ in row] for row in grid]
    for cells in _components(grid):
        replacement = 8 if _encloses_hole(cells) else 4
        for r, c in cells:
            out[r][c] = replacement
    return out
