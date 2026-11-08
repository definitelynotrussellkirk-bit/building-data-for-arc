"""Blind solution for the visible ARC examples.

Rotate every non-background, non-marker cell 90 degrees clockwise around the
first row-major color-6 marker.  Cells landing outside the canvas are clipped.
Only the selected marker is retained.
"""


def solve(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0

    pivots = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    if not pivots:
        return [row[:] for row in grid]

    pr, pc = pivots[0]
    out = [[0 for _ in range(w)] for _ in range(h)]
    out[pr][pc] = 6

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 6):
                continue
            # Relative (dr, dc) -> clockwise (dc, -dr).
            nr = pr + (c - pc)
            nc = pc - (r - pr)
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = value

    return out
