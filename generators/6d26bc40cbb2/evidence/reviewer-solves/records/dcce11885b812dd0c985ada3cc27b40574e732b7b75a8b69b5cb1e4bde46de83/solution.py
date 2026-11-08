def solve(grid):
    """Copy the non-marker pattern from one 9-anchor to the other."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    colored = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]

    out = [row[:] for row in grid]
    for r, c in anchors:
        out[r][c] = 0

    if len(anchors) != 2 or not colored:
        return out

    # The source anchor is the one closest to the existing colored pattern.
    # Sum distances rather than relying on a single nearest pixel.
    def distance_score(anchor):
        ar, ac = anchor
        return sum(abs(r - ar) + abs(c - ac) for r, c, _ in colored)

    source, target = sorted(anchors, key=distance_score)
    dr = target[0] - source[0]
    dc = target[1] - source[1]

    for r, c, value in colored:
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = value

    return out
