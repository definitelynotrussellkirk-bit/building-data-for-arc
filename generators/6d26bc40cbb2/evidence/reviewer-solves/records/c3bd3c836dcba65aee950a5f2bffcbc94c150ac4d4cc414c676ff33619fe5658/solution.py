from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Remove the two color-9 anchors and translate-copy the colored payload.

    The translation vector points from the first anchor in row-major order to
    the second.  Cells shifted outside the canvas are clipped.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    anchors = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9]
    if len(anchors) != 2:
        raise ValueError(f"expected exactly two color-9 anchors, found {len(anchors)}")
    (r1, c1), (r2, c2) = anchors
    dr, dc = r2 - r1, c2 - c1

    out = [[0 if value == 9 else value for value in row] for row in grid]
    payload = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 9)
    ]
    for r, c, value in payload:
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = value
    return out
