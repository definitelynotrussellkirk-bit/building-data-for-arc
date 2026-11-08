"""Visible-example-only solver for the blind episode."""
from collections import deque


def solve(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    objects = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            color = grid[r][c]
            seen[r][c] = True
            q = deque([(r, c)])
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            objects.append(cells)
    objects.sort(key=lambda cells: (len(cells), min(cells)))
    out = [[0] * w for _ in range(h)]
    for value, cells in zip((2, 4, 8), objects):
        for r, c in cells:
            out[r][c] = value
    return out
