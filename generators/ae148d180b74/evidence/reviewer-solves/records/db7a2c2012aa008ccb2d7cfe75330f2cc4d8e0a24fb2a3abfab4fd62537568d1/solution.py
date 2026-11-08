"""Visible-example hypothesis: paint one shortest 2-to-3 path with 8."""
from collections import deque


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    sources = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    targets = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if len(sources) != 1 or len(targets) != 1:
        raise ValueError("expected exactly one marker of each color")
    start, end = sources[0], targets[0]
    parent = {start: None}
    queue = deque([start])
    while queue and end not in parent:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            n = (r + dr, c + dc)
            if (0 <= n[0] < h and 0 <= n[1] < w
                    and grid[n[0]][n[1]] in (0, 2, 3) and n not in parent):
                parent[n] = (r, c)
                queue.append(n)
    if end not in parent:
        return out
    cur = parent[end]
    while cur is not None and cur != start:
        out[cur[0]][cur[1]] = 8
        cur = parent[cur]
    return out
