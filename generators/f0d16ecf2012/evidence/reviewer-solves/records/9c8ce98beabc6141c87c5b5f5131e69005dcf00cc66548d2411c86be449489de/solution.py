from __future__ import annotations

from collections import deque


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
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
            found.append((color, cells))
    return found


def solve(grid):
    """Slide every nonzero/non-9 4-connected component east independently."""
    h, w = len(grid), len(grid[0])
    walls = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    }
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in walls:
        out[r][c] = 9

    for color, original_cells in _components(grid):
        static_occupied = walls | set(original_cells)
        cells = list(original_cells)
        while True:
            current = set(cells)
            shifted = [(r, c + 1) for r, c in cells]
            legal = all(
                0 <= r < h
                and 0 <= c < w
                and ((r, c) not in static_occupied or (r, c) in current)
                for r, c in shifted
            )
            if not legal:
                break
            cells = shifted
        for r, c in cells:
            out[r][c] = color
    return out
