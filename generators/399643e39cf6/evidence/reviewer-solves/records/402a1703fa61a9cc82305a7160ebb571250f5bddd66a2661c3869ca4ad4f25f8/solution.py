"""Visible-example solution for reviewer solve 399643e39cf6."""
from copy import deepcopy


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 9) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            out.append((color, tuple(cells)))
    return out


def solve(grid):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    markers = sorted(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    )
    if len(markers) != 2:
        return out
    (r1, c1), (r2, c2) = markers
    dr, dc = r2 - r1, c2 - c1
    for r, c in markers:
        out[r][c] = 0

    comps = _components(grid)
    if not comps:
        return out

    def key(item):
        color, cells = item
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        return len(cells), top, left, color

    color, cells = min(comps, key=key)
    for r, c in cells:
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = color
    return out
