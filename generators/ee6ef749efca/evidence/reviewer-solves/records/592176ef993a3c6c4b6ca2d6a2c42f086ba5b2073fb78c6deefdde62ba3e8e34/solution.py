"""Visible-example solution for the blind ARC episode."""

from collections import deque


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            comp = []
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append(comp)
    return out


def solve(grid):
    """Copy the largest magenta object at every red top-left marker."""
    h, w = len(grid), len(grid[0])
    magenta_components = _components(grid, 6)
    if not magenta_components:
        return [row[:] for row in grid]

    source = max(magenta_components, key=len)
    min_r = min(r for r, _ in source)
    min_c = min(c for _, c in source)
    shape = [(r - min_r, c - min_c) for r, c in source]
    markers = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 2
    ]

    result = [[0 for _ in range(w)] for _ in range(h)]
    for anchor_r, anchor_c in markers:
        for dr, dc in shape:
            r, c = anchor_r + dr, anchor_c + dc
            if 0 <= r < h and 0 <= c < w:
                result[r][c] = 6
    return result
