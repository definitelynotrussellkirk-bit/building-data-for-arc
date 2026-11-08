"""Visible-only solution for blind task bedcbc1cb6fb."""


def solve(grid):
    out = [row[:] for row in grid]
    ones = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if not ones:
        return out

    r0 = min(r for r, _ in ones)
    r1 = max(r for r, _ in ones)
    c0 = min(c for _, c in ones)
    c1 = max(c for _, c in ones)

    markers = sorted(
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1) and not (r0 <= r <= r1 and c0 <= c <= c1)
    )
    colors = [value for _, _, value in markers]
    if not colors:
        return out

    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            layer = min(r - (r0 + 1), (r1 - 1) - r, c - (c0 + 1), (c1 - 1) - c)
            out[r][c] = colors[min(layer, len(colors) - 1)]
    return out
