def solve(grid):
    """Expand the two colored dots into stacked rectangular frame halves."""
    h = len(grid)
    w = len(grid[0])
    dots = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if len(dots) != 2:
        raise ValueError("expected exactly two colored cells")

    dots.sort(key=lambda item: item[0])
    upper_row, _, upper_color = dots[0]
    lower_row, _, lower_color = dots[1]
    split = h // 2
    if not (upper_row < split <= lower_row):
        raise ValueError("expected one dot in each horizontal half")

    out = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        color = upper_color if r < split else lower_color
        out[r][0] = color
        out[r][w - 1] = color

    for c in range(w):
        out[0][c] = upper_color
        out[upper_row][c] = upper_color
        out[lower_row][c] = lower_color
        out[h - 1][c] = lower_color
    return out
