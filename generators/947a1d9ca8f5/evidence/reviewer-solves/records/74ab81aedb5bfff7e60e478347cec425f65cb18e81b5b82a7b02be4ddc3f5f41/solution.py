from collections import deque


def _components(grid):
    """Return 4-connected components excluding background 0 and marker 9."""
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] in (0, 9):
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc, grid[rr][cc]))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] not in (0, 9)
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append(cells)
    return out


def solve(grid):
    """Copy the smallest non-marker object at every color-9 anchor."""
    h, w = len(grid), len(grid[0])
    components = _components(grid)
    if not components:
        return [[0] * w for _ in range(h)]

    # The demonstrations consistently identify the smaller object as the stamp.
    stamp = min(components, key=lambda cells: len(cells))
    top = min(r for r, _, _ in stamp)
    left = min(c for _, c, _ in stamp)
    normalized = [(r - top, c - left, color) for r, c, color in stamp]

    result = [[0] * w for _ in range(h)]
    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    for ar, ac in anchors:
        for dr, dc, color in normalized:
            rr, cc = ar + dr, ac + dc
            if 0 <= rr < h and 0 <= cc < w:
                result[rr][cc] = color
    return result
