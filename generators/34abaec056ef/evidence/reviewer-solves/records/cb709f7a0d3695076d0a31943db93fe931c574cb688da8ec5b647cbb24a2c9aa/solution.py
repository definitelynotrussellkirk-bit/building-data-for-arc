def solve(grid):
    """Project local color-8 cells around the ordered 2-3-4 frame."""
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (2, 3, 4):
                positions.setdefault(value, []).append((r, c))

    if any(len(positions.get(color, ())) != 1 for color in (2, 3, 4)):
        raise ValueError("expected one cell of each frame color 2, 3 and 4")

    origin = positions[2][0]
    x_tip = positions[3][0]
    y_tip = positions[4][0]
    vx = (x_tip[0] - origin[0], x_tip[1] - origin[1])
    vy = (y_tip[0] - origin[0], y_tip[1] - origin[1])

    height = len(grid)
    width = len(grid[0]) if grid else 0
    out = [[0] * 3 for _ in range(3)]
    for out_r, y in enumerate((-1, 0, 1)):
        for out_c, x in enumerate((-1, 0, 1)):
            r = origin[0] + x * vx[0] + y * vy[0]
            c = origin[1] + x * vx[1] + y * vy[1]
            if 0 <= r < height and 0 <= c < width and grid[r][c] == 8:
                out[out_r][out_c] = 8
    return out
