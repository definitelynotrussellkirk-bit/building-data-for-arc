"""Trace the ray inferred from the visible demonstration pairs."""


def solve(grid):
    h, w = len(grid), len(grid[0])
    result = [[0] * w for _ in range(h)]
    sources = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(sources) != 1:
        raise ValueError("Expected one boundary source")
    r, c = sources[0]
    if r == 0:
        dr, dc = 1, 0
    elif r == h - 1:
        dr, dc = -1, 0
    elif c == 0:
        dr, dc = 0, 1
    elif c == w - 1:
        dr, dc = 0, -1
    else:
        raise ValueError("Source is not on the boundary")
    seen = set()
    while True:
        r, c = r + dr, c + dc
        if not (0 <= r < h and 0 <= c < w):
            break
        if (r, c, dr, dc) in seen or grid[r][c] in (2, 5):
            break
        seen.add((r, c, dr, dc))
        result[r][c] = 8
        if grid[r][c] == 6:
            dr, dc = dc, dr
        elif grid[r][c] == 7:
            dr, dc = -dc, -dr
    return result
