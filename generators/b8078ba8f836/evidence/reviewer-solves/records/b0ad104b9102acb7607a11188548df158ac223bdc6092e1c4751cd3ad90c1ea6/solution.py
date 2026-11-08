"""Visible-example solution for the post-repair episode."""


def solve(grid):
    out = [row[:] for row in grid]
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r1][c] = color
        elif c1 == c2:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                out[r][c1] = color
    return out
