from __future__ import annotations

from collections import deque


def solve(grid):
    """Fill each monochrome 4-connected nonzero component's tight rectangle."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [[0 for _ in range(w)] for _ in range(h)]
    seen = set()

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
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
                        todo.append((nr, nc))

            r1 = min(rr for rr, _ in cells)
            r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            c2 = max(cc for _, cc in cells)
            for rr in range(r1, r2 + 1):
                for cc in range(c1, c2 + 1):
                    out[rr][cc] = color
    return out
