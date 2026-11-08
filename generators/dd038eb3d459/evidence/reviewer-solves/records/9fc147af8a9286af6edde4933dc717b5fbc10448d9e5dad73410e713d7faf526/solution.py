"""Visible-example solution for ARC task dd038eb3d459."""


def _crop_mask(grid, color):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [
        [1 if grid[r][c] == color else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _rotate_clockwise(mask):
    return [list(row) for row in zip(*mask[::-1])]


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    if grid[0][0] == 1:
        turns = 0
    elif grid[0][width - 1] == 1:
        turns = 1
    elif grid[height - 1][width - 1] == 1:
        turns = 2
    elif grid[height - 1][0] == 1:
        turns = 3
    else:
        raise ValueError("expected one blue marker in a canvas corner")

    green = _crop_mask(grid, 3)
    red = _crop_mask(grid, 2)
    for _ in range(turns):
        green = _rotate_clockwise(green)

    out_h = max(len(green), len(red))
    out_w = max(len(green[0]), len(red[0]))
    output = []
    for r in range(out_h):
        row = []
        for c in range(out_w):
            green_on = r < len(green) and c < len(green[0]) and green[r][c]
            red_on = r < len(red) and c < len(red[0]) and red[r][c]
            row.append(8 if bool(green_on) != bool(red_on) else 0)
        output.append(row)
    return output
