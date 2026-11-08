"""Visible-only solution for blind task f06d31332595."""


def solve(grid):
    out = [row[:] for row in grid]
    h = len(grid)
    w = len(grid[0]) if h else 0

    # The full-height color-5 column is the mirror axis. Copy every
    # non-background cell from its left side to the reflected position.
    axes = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(axes) != 1:
        raise ValueError(f"expected exactly one full-height color-5 axis, got {axes}")
    axis = axes[0]

    for r in range(h):
        for c in range(axis):
            value = grid[r][c]
            if value != 0:
                reflected = 2 * axis - c
                if 0 <= reflected < w:
                    out[r][reflected] = value
    return out
