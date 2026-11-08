from __future__ import annotations


def solve(grid):
    """Expand exact diagonal color pairs into bounding-box outlines."""
    out = [list(row) for row in grid]
    positions = {}
    order = []

    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0:
                continue
            if color not in positions:
                positions[color] = []
                order.append(color)
            positions[color].append((r, c))

    for color in order:
        cells = positions[color]
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2 or c1 == c2:
            continue
        top, bottom = sorted((r1, r2))
        left, right = sorted((c1, c2))
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if r in (top, bottom) or c in (left, right):
                    out[r][c] = color
    return out
