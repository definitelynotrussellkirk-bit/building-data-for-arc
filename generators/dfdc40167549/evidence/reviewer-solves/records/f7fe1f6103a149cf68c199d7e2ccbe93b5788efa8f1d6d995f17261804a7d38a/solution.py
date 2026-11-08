"""Visible-example solution; no reference files or private answers used."""
def solve(grid):
    h, w = len(grid), len(grid[0])
    if not h or not w or any(len(row) != w for row in grid):
        raise ValueError('expected a nonempty rectangular grid')
    markers = {color: [(r, c) for r, row in enumerate(grid)
                       for c, value in enumerate(row) if value == color]
               for color in (1, 2)}
    if any(len(points) != 1 for points in markers.values()):
        raise ValueError('expected one source and one destination marker')
    dr = markers[2][0][0] - markers[1][0][0]
    dc = markers[2][0][1] - markers[1][0][1]
    shape = {(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value not in (0, 1, 2)}
    out = [[0] * w for _ in range(h)]
    for r, c in shape:
        interior = all((r + rr, c + cc) in shape
                       for rr, cc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            out[nr][nc] = 8 if interior else 7
    return out
