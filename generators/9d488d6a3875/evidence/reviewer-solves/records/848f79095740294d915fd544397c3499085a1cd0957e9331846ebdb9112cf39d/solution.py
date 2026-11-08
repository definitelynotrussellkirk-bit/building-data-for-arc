from collections import defaultdict


def solve(grid):
    """Connect each same-colour endpoint pair with an axis-aligned segment."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    for value, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r1][c] = value
        elif c1 == c2:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                out[r][c1] = value

    return out
