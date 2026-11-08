from collections import deque


def _components(grid, color):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            comp = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            yield comp


def solve(grid):
    out = [row[:] for row in grid]
    missing_to_color = {
        (1, 1): 2,
        (1, 0): 3,
        (0, 1): 4,
        (0, 0): 8,
    }
    for comp in _components(grid, 1):
        if len(comp) != 3:
            continue
        r0 = min(r for r, _ in comp)
        r1 = max(r for r, _ in comp)
        c0 = min(c for _, c in comp)
        c1 = max(c for _, c in comp)
        if r1 - r0 != 1 or c1 - c0 != 1:
            continue
        normalized = {(r - r0, c - c0) for r, c in comp}
        missing = {(0, 0), (0, 1), (1, 0), (1, 1)} - normalized
        if len(missing) != 1:
            continue
        color = missing_to_color[next(iter(missing))]
        for r, c in comp:
            out[r][c] = color
    return out
