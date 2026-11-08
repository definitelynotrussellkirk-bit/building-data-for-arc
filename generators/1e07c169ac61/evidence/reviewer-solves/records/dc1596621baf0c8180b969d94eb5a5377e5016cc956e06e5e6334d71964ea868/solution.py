def solve(grid):
    """Rotate every nonzero non-9 cell 90 degrees CW about the unique 9."""
    h = len(grid)
    w = len(grid[0])
    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(anchors) != 1:
        raise ValueError(f"expected one color-9 anchor, found {anchors}")
    ar, ac = anchors[0]
    out = [[0 for _ in range(w)] for _ in range(h)]
    out[ar][ac] = 9
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            rr = ar + (c - ac)
            cc = ac - (r - ar)
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out
