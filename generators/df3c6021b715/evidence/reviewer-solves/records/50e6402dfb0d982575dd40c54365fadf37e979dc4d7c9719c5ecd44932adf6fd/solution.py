"""Visible-example solution for df3c6021b715."""


def solve(grid):
    h = len(grid)
    w = len(grid[0])
    dots = sorted(
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    )
    if len(dots) != 2:
        raise ValueError("expected exactly two nonzero cells")

    (upper_row, _upper_col, upper_color), (lower_row, _lower_col, lower_color) = dots
    split = h // 2
    output = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        if r < split:
            color = upper_color
            horizontal = r == 0 or r == upper_row
        else:
            color = lower_color
            horizontal = r == lower_row or r == h - 1
        for c in range(w):
            if horizontal or c == 0 or c == w - 1:
                output[r][c] = color
    return output
