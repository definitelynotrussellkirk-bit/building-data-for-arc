from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Stamp the tight color-2 template in color 8 at every color-3 cell."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    template = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if not template:
        return [[0] * w for _ in range(h)]
    r0 = min(r for r, _ in template)
    c0 = min(c for _, c in template)
    offsets = [(r - r0, c - c0) for r, c in template]
    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    out = [[0] * w for _ in range(h)]
    for r, c in anchors:
        for dr, dc in offsets:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 8
    return out
