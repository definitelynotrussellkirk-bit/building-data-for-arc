from collections import defaultdict


def solve(grid):
    """Connect an unobstructed aligned pair of equal nonzero cells."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    # The examples use exactly two endpoints for every potentially drawn color.
    # Test path clearance against the original grid so one new segment cannot
    # accidentally enable or block another segment.
    for value, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            lo, hi = sorted((c1, c2))
            if all(grid[r1][c] == 0 for c in range(lo + 1, hi)):
                for c in range(lo + 1, hi):
                    out[r1][c] = value
        elif c1 == c2:
            lo, hi = sorted((r1, r2))
            if all(grid[r][c1] == 0 for r in range(lo + 1, hi)):
                for r in range(lo + 1, hi):
                    out[r][c1] = value

    return out
