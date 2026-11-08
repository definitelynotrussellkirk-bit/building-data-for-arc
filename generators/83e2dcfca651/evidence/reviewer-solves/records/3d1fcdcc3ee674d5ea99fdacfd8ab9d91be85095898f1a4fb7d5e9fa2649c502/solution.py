def solve(grid):
    """Copy the green object by the signed blue-to-red displacement."""
    out = [row[:] for row in grid]
    blue = None
    red = None
    green = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 1:
                blue = (r, c)
            elif value == 2:
                red = (r, c)
            elif value == 3:
                green.append((r, c))
    if blue is None or red is None:
        return out
    dr = red[0] - blue[0]
    dc = red[1] - blue[1]
    height = len(out)
    width = len(out[0]) if out else 0
    for r, c in green:
        rr, cc = r + dr, c + dc
        if 0 <= rr < height and 0 <= cc < width:
            out[rr][cc] = 2
    return out
