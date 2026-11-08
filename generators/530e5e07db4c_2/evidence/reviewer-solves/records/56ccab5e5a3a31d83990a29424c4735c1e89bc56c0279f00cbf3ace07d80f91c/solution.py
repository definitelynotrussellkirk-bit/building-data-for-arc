"""Visible-example solution for the exposed post-repair episode."""
from collections import deque


def solve(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    greens = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3}
    if len(reds) != 1 or len(greens) != 1:
        return out

    start = reds[0]
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and (nr, nc) not in seen
                and grid[nr][nc] in (2, 3, 5)
            ):
                seen.add((nr, nc))
                queue.append((nr, nc))

    if not (seen & greens):
        return out
    for r, c in seen:
        if grid[r][c] == 5:
            out[r][c] = 4
    return out
