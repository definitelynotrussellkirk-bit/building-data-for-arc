from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill the overlap of the 3x3 neighborhoods of the green cell and the
    nearest red cell; ties are resolved in row-major order.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    green = None
    reds: list[tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 3:
                green = (r, c)
            elif value == 2:
                reds.append((r, c))

    out = [[0 for _ in range(w)] for _ in range(h)]
    if green is None or not reds:
        return out

    gr, gc = green
    rr, rc = min(
        reds,
        key=lambda p: (max(abs(p[0] - gr), abs(p[1] - gc)),
                       abs(p[0] - gr) + abs(p[1] - gc),
                       p[0], p[1]),
    )

    r_lo = max(0, gr - 1, rr - 1)
    r_hi = min(h - 1, gr + 1, rr + 1)
    c_lo = max(0, gc - 1, rc - 1)
    c_hi = min(w - 1, gc + 1, rc + 1)
    if r_lo <= r_hi and c_lo <= c_hi:
        for r in range(r_lo, r_hi + 1):
            for c in range(c_lo, c_hi + 1):
                out[r][c] = 8
    return out
