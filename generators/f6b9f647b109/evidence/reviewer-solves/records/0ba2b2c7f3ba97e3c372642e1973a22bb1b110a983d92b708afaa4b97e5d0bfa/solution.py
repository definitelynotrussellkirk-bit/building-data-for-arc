"""Visible-example solution for the blind ARC episode."""


def _sign(value):
    return (value > 0) - (value < 0)


def solve(grid):
    """Connect red (2) to blue (1) with the example-defined green path."""
    out = [row[:] for row in grid]
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (1, 2):
                positions.setdefault(value, []).append((r, c))

    if len(positions.get(1, [])) != 1 or len(positions.get(2, [])) != 1:
        raise ValueError("expected exactly one blue cell and one red cell")

    blue_r, blue_c = positions[1][0]
    r, c = positions[2][0]
    dr = blue_r - r
    dc = blue_c - c
    row_step = _sign(dr)
    col_step = _sign(dc)
    row_distance = abs(dr)
    col_distance = abs(dc)
    diagonal_steps = min(row_distance, col_distance)
    straight_steps = abs(row_distance - col_distance)

    def advance(step_r, step_c):
        nonlocal r, c
        r += step_r
        c += step_c
        if (r, c) != (blue_r, blue_c):
            out[r][c] = 3

    # The visible examples anchor the path at red: one diagonal step first,
    # then all excess motion on the dominant axis, then the remaining diagonal.
    if diagonal_steps:
        advance(row_step, col_step)

    if row_distance > col_distance:
        for _ in range(straight_steps):
            advance(row_step, 0)
    elif col_distance > row_distance:
        for _ in range(straight_steps):
            advance(0, col_step)

    for _ in range(max(0, diagonal_steps - 1)):
        advance(row_step, col_step)

    return out
