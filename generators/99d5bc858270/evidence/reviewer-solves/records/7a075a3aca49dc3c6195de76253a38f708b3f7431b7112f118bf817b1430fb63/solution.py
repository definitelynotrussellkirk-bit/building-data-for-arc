from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Cast color-4 rays from every colored object away from the border light."""
    h = len(grid)
    if h == 0:
        return []
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        raise ValueError("grid must be non-empty and rectangular")

    lights = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4 and (r in (0, h - 1) or c in (0, w - 1))
    ]
    if len(lights) != 1:
        raise ValueError(f"expected one border light of color 4, found {len(lights)}")
    lr, lc = lights[0]

    # The two corner examples show that a side-border placement takes priority
    # over top/bottom: left means rays go right, right means rays go left.
    if lc == 0:
        dr, dc = 0, 1
    elif lc == w - 1:
        dr, dc = 0, -1
    elif lr == 0:
        dr, dc = 1, 0
    elif lr == h - 1:
        dr, dc = -1, 0
    else:
        raise ValueError("the color-4 light must be on the border")

    casters = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (lr, lc)
    ]

    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c, _ in casters:
        rr, cc = r, c
        while 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = 4
            rr += dr
            cc += dc

    # Original objects sit in front of all rays; the border light disappears.
    for r, c, value in casters:
        out[r][c] = value
    return out
