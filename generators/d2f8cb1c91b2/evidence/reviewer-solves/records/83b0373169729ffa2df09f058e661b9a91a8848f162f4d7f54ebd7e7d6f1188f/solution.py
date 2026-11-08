"""Visible-example solution for d2f8cb1c91b2."""
from __future__ import annotations


def _transform(grid, code):
    n = len(grid)
    out = [[0] * n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            if code == "id":
                rr, cc = r, c
            elif code == "r1":
                rr, cc = c, n - 1 - r
            elif code == "r2":
                rr, cc = n - 1 - r, n - 1 - c
            elif code == "r3":
                rr, cc = n - 1 - c, r
            elif code == "fh":
                rr, cc = r, n - 1 - c
            elif code == "fv":
                rr, cc = n - 1 - r, c
            elif code == "tr":
                rr, cc = c, r
            elif code == "atr":
                rr, cc = n - 1 - c, n - 1 - r
            else:
                raise ValueError(code)
            out[rr][cc] = grid[r][c]
    return out


def solve(grid):
    """Infer panel-1 -> panel-2 geometry, transform panel 3, merge with panel 4."""
    if len(grid) != 3 or any(len(row) != 15 for row in grid):
        raise ValueError("expected a 3x15 grid")
    panels = [
        [row[left:left + 3] for row in grid]
        for left in (0, 4, 8, 12)
    ]
    a, b, x, y = panels
    transform_order = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
    matches = [code for code in transform_order if _transform(a, code) == b]
    if not matches:
        raise ValueError("no geometric transform maps the first panel to the second")
    tx = _transform(x, matches[0])
    out = [[0] * 3 for _ in range(3)]
    for r in range(3):
        for c in range(3):
            u, v = tx[r][c], y[r][c]
            if u == 0:
                out[r][c] = v
            elif v == 0 or u == v:
                out[r][c] = u
            else:
                out[r][c] = 9
    return out
