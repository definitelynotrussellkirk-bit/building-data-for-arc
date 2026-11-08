"""Explicit audit rivals; neither is used as the output authority."""


def target_centers(grid):
    return [(r, c) for r in range(1, len(grid) - 1)
            for c in range(len(grid[0]))
            if grid[r][c] == 0 and grid[r - 1][c] == grid[r + 1][c] == 7]


def cap_two_per_column(grid):
    """Perform the local rule, but process at most two targets per column."""
    out = [row[:] for row in grid]
    counts = {}
    for r, c in target_centers(grid):
        counts[c] = counts.get(c, 0) + 1
        if counts[c] <= 2:
            out[r][c] = 4
    return out


def shared_chains_only_at_edges(grid):
    """A structural shortcut suggested by the fixed contrast footprint."""
    out = [row[:] for row in grid]
    targets = target_centers(grid)
    counts = {}
    for r, c in targets:
        counts[c] = counts.get(c, 0) + 1
    for r, c in targets:
        if counts[c] == 1 or c in (0, len(grid[0]) - 1):
            out[r][c] = 4
    return out
