"""Visible-example solution for the blind ARC task."""


def _period_rows(grid):
    h = len(grid)
    for p in range(1, h + 1):
        if all(grid[r] == grid[r % p] for r in range(h)):
            return p
    return h


def _period_cols(grid):
    h, w = len(grid), len(grid[0])
    for p in range(1, w + 1):
        if all(grid[r][c] == grid[r][c % p] for r in range(h) for c in range(w)):
            return p
    return w


def solve(grid):
    """Remove the L-shaped padding, shift the motif left once, and retile it."""
    if not grid or not grid[0]:
        return []

    height, width = len(grid), len(grid[0])
    pad = grid[-1][-1]

    active_h = height
    while active_h > 0 and all(v == pad for v in grid[active_h - 1]):
        active_h -= 1

    active_w = width
    while active_w > 0 and all(grid[r][active_w - 1] == pad for r in range(height)):
        active_w -= 1

    motif = [row[:active_w] for row in grid[:active_h]]
    if not motif or not motif[0]:
        return [row[:] for row in grid]

    row_period = _period_rows(motif)
    col_period = _period_cols(motif)

    return [
        [motif[r % row_period][(c + 1) % col_period] for c in range(width)]
        for r in range(height)
    ]
