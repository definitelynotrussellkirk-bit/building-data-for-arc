"""Blind solution for ee6ef749efca, derived only from visible examples."""

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
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
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
            out.append(cells)
    return out


def solve(grid):
    """Stamp the largest 6-component at every red (2) top-left marker."""
    h, w = len(grid), len(grid[0])
    six_components = _components(grid, 6)
    if not six_components:
        return [[0 for _ in range(w)] for _ in range(h)]

    template = max(six_components, key=len)
    top = min(r for r, _ in template)
    left = min(c for _, c in template)
    offsets = [(r - top, c - left) for r, c in template]

    result = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2:
                continue
            for dr, dc in offsets:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    result[rr][cc] = 6
    return result
