"""Visible-example-only solution for the blind ARC task.

The red boundary cell emits an inward ray.  Azure marks empty cells traversed
by the ray; green and yellow cells are mirrors and gray cells absorb the ray.
"""


def solve(grid):
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    red = [(r, c) for r, row in enumerate(out) for c, value in enumerate(row) if value == 2]
    if len(red) != 1:
        return out

    r, c = red[0]
    inward = []
    if r == 0:
        inward.append((1, 0))
    if r == height - 1:
        inward.append((-1, 0))
    if c == 0:
        inward.append((0, 1))
    if c == width - 1:
        inward.append((0, -1))

    # The observed task places the source on one non-corner boundary side.
    # Keep a deterministic fallback for malformed/corner cases.
    if not inward:
        return out
    dr, dc = inward[0]

    seen = set()
    while True:
        state = (r, c, dr, dc)
        if state in seen:
            # A closed mirror loop has already painted every traversed cell.
            break
        seen.add(state)

        r += dr
        c += dc
        if not (0 <= r < height and 0 <= c < width):
            break

        value = out[r][c]
        if value == 0:
            out[r][c] = 8
        elif value == 3:  # slash mirror: /
            dr, dc = -dc, -dr
        elif value == 4:  # backslash mirror: \
            dr, dc = dc, dr
        elif value == 5:
            break
        # Other nonzero cells are preserved and traversed without changing
        # direction; this is only a defensive fallback outside the examples.

    return out
