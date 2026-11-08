"""Visible-example solution for blind ARC task 50385c1a773f."""


def _paint_between(out, a, b):
    """Paint zero cells strictly between axis-aligned endpoints a and b."""
    r1, c1 = a
    r2, c2 = b
    if r1 == r2:
        lo, hi = sorted((c1, c2))
        for c in range(lo + 1, hi):
            if out[r1][c] == 0:
                out[r1][c] = 8
        return "horizontal"
    if c1 == c2:
        lo, hi = sorted((r1, r2))
        for r in range(lo + 1, hi):
            if out[r][c1] == 0:
                out[r][c1] = 8
        return "vertical"
    raise ValueError("endpoints are not axis-aligned")


def solve(grid):
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    coloured = {}
    grey = []
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value in (2, 3, 4):
                coloured[value] = (r, c)
            elif value == 5:
                grey.append((r, c))

    if 2 not in coloured:
        return out

    current = coloured[2]
    unused = {value: pos for value, pos in coloured.items() if value != 2}
    last_axis = None

    # Follow the uniquely axis-aligned chain of coloured waypoints.
    while unused:
        aligned = [
            (value, pos)
            for value, pos in unused.items()
            if pos[0] == current[0] or pos[1] == current[1]
        ]
        if not aligned:
            break
        # Visible examples make this unique; nearest is a deterministic fallback.
        value, nxt = min(
            aligned,
            key=lambda item: abs(item[1][0] - current[0])
            + abs(item[1][1] - current[1]),
        )
        last_axis = _paint_between(out, current, nxt)
        current = nxt
        del unused[value]

    # The terminal waypoint connects to an aligned grey object when present.
    aligned_grey = [
        pos for pos in grey if pos[0] == current[0] or pos[1] == current[1]
    ]
    if aligned_grey:
        target = min(
            aligned_grey,
            key=lambda pos: abs(pos[0] - current[0]) + abs(pos[1] - current[1]),
        )
        _paint_between(out, current, target)
        return out

    # Otherwise the grey object indicates which side of the terminal waypoint
    # the final, perpendicular ray should use; the examples extend that ray to
    # the grid edge.
    if grey and last_axis == "horizontal":
        delta = sum(r - current[0] for r, _ in grey)
        step = 1 if delta >= 0 else -1
        r = current[0] + step
        while 0 <= r < height:
            if out[r][current[1]] == 0:
                out[r][current[1]] = 8
            r += step
    elif grey and last_axis == "vertical":
        delta = sum(c - current[1] for _, c in grey)
        step = 1 if delta >= 0 else -1
        c = current[1] + step
        while 0 <= c < width:
            if out[current[0]][c] == 0:
                out[current[0]][c] = 8
            c += step

    return out
