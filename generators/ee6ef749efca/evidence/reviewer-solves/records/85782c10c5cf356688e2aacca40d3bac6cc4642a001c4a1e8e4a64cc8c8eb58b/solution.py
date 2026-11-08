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
                cr, cc = q.popleft()
                comp.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
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
    """Stamp the largest magenta object at every red anchor."""
    h, w = len(grid), len(grid[0])
    components = _components(grid, 6)
    if not components:
        return [[0 for _ in range(w)] for _ in range(h)]

    # The demonstrations use the largest 4-connected magenta object as the
    # template.  Preserve its orientation and normalize its top-left cell to
    # offset (0, 0).
    template = max(components, key=lambda comp: (len(comp), -min(comp)))
    min_r = min(r for r, _ in template)
    min_c = min(c for _, c in template)
    offsets = [(r - min_r, c - min_c) for r, c in template]

    result = [[0 for _ in range(w)] for _ in range(h)]
    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    for ar, ac in anchors:
        for dr, dc in offsets:
            r, c = ar + dr, ac + dc
            if 0 <= r < h and 0 <= c < w:
                result[r][c] = 6
    return result
