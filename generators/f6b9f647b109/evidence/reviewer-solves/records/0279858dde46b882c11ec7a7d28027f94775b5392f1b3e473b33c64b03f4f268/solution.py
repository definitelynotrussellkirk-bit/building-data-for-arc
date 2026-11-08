from copy import deepcopy


def _sign(value):
    return (value > 0) - (value < 0)


def solve(grid):
    """Connect red (2) to blue (1) with the demonstrated green route."""
    out = deepcopy(grid)
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (1, 2):
                positions[value] = (r, c)

    if 1 not in positions or 2 not in positions:
        return out

    r, c = positions[2]
    target_r, target_c = positions[1]
    step_r = _sign(target_r - r)
    step_c = _sign(target_c - c)

    def advance(delta_r, delta_c):
        nonlocal r, c
        r += delta_r
        c += delta_c
        if (r, c) != (target_r, target_c):
            out[r][c] = 3

    # The examples consistently orient the route from red toward blue:
    # one diagonal step, then the full unmatched major-axis run, then
    # the remaining diagonal steps.
    if r != target_r and c != target_c:
        advance(step_r, step_c)

    while abs(target_r - r) > abs(target_c - c):
        advance(step_r, 0)
    while abs(target_c - c) > abs(target_r - r):
        advance(0, step_c)
    while (r, c) != (target_r, target_c):
        advance(step_r, step_c)

    return out
