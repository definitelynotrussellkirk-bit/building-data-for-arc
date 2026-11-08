"""Visible-only ARC solution for task 4a6d26e0b6ae."""


def solve(grid):
    """Fill the single-cell gap between each same-colour aligned pair."""
    out = [row[:] for row in grid]
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))

    for value, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2 and abs(c1 - c2) == 2:
            out[r1][(c1 + c2) // 2] = value
        elif c1 == c2 and abs(r1 - r2) == 2:
            out[(r1 + r2) // 2][c1] = value
    return out
