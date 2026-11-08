from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Mirror every non-guide colored cell across both 5/6 guide axes."""
    h = len(grid)
    w = len(grid[0])
    guide_rows = [
        r
        for r, row in enumerate(grid)
        if all(value in (5, 6) for value in row)
        and sum(value == 6 for value in row) >= w - 1
    ]
    guide_cols = [
        c
        for c in range(w)
        if all(grid[r][c] in (5, 6) for r in range(h))
        and sum(grid[r][c] == 5 for r in range(h)) >= h - 1
    ]
    if len(guide_rows) != 1 or len(guide_cols) != 1:
        raise ValueError("expected one horizontal 6-guide and one vertical 5-guide")
    axis_r, axis_c = guide_rows[0], guide_cols[0]

    out = [row[:] for row in grid]
    motif = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    ]
    for r, c, value in motif:
        reflected = (
            (r, 2 * axis_c - c),
            (2 * axis_r - r, c),
            (2 * axis_r - r, 2 * axis_c - c),
        )
        for rr, cc in reflected:
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out
