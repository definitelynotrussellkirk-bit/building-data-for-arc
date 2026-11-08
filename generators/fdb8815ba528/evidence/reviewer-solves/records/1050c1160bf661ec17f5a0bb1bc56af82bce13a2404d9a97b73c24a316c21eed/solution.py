"""Visible-example solution for fdb8815ba528."""
from collections import deque


def solve(grid):
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    seen = set()

    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            for r in range(top, bottom + 1):
                for c in range(left, right + 1):
                    if r in (top, bottom) or c in (left, right):
                        out[r][c] = color
    return out
