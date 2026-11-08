from collections import defaultdict


def solve(grid):
    """Connect an exactly-two same-color pair when it is axis-aligned."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions[color].append((r, c))

    for color, points in positions.items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r1][c] = color
        elif c1 == c2:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                out[r][c1] = color
    return out
