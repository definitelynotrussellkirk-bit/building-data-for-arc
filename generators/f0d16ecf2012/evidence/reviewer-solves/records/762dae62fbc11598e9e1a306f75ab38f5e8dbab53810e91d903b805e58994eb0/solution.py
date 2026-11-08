from __future__ import annotations

from collections import deque


def solve(grid):
    """Move each non-wall 4-connected color component east until blocked."""
    h = len(grid)
    w = len(grid[0])
    walls = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9}
    seen = set()
    components = []

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 9) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append((color, cells))

    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in walls:
        out[r][c] = 9

    for color, original_cells in components:
        cells = list(original_cells)
        while True:
            shifted = [(r, c + 1) for r, c in cells]
            if any(c >= w or (r, c) in walls for r, c in shifted):
                break
            cells = shifted
        for r, c in cells:
            out[r][c] = color

    return out
