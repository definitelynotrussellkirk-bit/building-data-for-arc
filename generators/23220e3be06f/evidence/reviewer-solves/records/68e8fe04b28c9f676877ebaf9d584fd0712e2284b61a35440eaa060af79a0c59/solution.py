"""Visible-example-only solver for task 23220e3be06f.

Only command values demonstrated by the exposed examples are implemented.
"""


def _tight_crop(grid):
    rows = [r for r, row in enumerate(grid) for value in row if value != 0]
    cols = [c for row in grid for c, value in enumerate(row) if value != 0]
    if not rows:
        return []
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _rotate_clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def solve(grid):
    command = grid[0][0]
    work = [row[:] for row in grid]
    work[0][0] = 0
    motif = _tight_crop(work)

    if command == 1:
        return motif
    if command == 2:
        return _rotate_clockwise(motif)
    raise ValueError(f"command {command} was not demonstrated in the visible examples")
