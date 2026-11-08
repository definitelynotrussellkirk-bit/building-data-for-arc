from collections import defaultdict


def solve(grid):
    """Fill the inclusive bounding rectangle of each repeated nonzero color."""
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    out = [list(row) for row in grid]
    for color, points in positions.items():
        if len(points) != 2:
            continue
        (r0, c0), (r1, c1) = points
        for r in range(min(r0, r1), max(r0, r1) + 1):
            for c in range(min(c0, c1), max(c0, c1) + 1):
                out[r][c] = color
    return out
