"""Visible-example solution: continue the observed blue displacement in red."""


def solve(grid):
    result = [list(row) for row in grid]
    points = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color == 1]
    if len(points) < 2:
        raise ValueError('At least two blue points are required')
    dr = points[1][0] - points[0][0]
    dc = points[1][1] - points[0][1]
    if (dr, dc) == (0, 0):
        raise ValueError('The displacement must be nonzero')
    r, c = points[-1]
    while True:
        r, c = r + dr, c + dc
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            break
        result[r][c] = 2
    return result
