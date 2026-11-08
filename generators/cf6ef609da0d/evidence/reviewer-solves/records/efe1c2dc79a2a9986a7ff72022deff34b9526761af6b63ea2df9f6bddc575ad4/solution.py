from collections import deque


def solve(grid):
    """Apply the inferred ARC transformation to a rectangular integer grid."""
    if not grid:
        return []
    h = len(grid)
    w = len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    seen = set()

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 6 or (r, c) in seen:
                continue

            component = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                component.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 6
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            if any(cr == cc for cr, cc in component):
                for cr, cc in component:
                    out[cr][cc] = 2

    return out
