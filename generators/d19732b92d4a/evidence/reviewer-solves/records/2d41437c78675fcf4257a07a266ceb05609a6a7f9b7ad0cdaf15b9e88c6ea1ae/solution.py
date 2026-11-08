from collections import defaultdict


def solve(grid):
    """Fill a blank midpoint between equal colors two diagonal steps apart."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    proposals = defaultdict(set)
    for value, cells in positions.items():
        for i, (r1, c1) in enumerate(cells):
            for r2, c2 in cells[i + 1 :]:
                if abs(r1 - r2) == 2 and abs(c1 - c2) == 2:
                    mr = (r1 + r2) // 2
                    mc = (c1 + c2) // 2
                    if grid[mr][mc] == 0:
                        proposals[(mr, mc)].add(value)

    # The examples contain unambiguous proposals.  Avoid inventing a winner if
    # an unseen input makes two colors compete for one blank midpoint.
    for (r, c), values in proposals.items():
        if len(values) == 1:
            out[r][c] = next(iter(values))

    return out
