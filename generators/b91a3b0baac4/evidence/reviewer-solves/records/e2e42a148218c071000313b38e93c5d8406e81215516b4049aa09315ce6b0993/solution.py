"""Visible-example solution for the post-repair corner-marker beam puzzle."""
from copy import deepcopy


def solve(grid):
    h, w = len(grid), len(grid[0])
    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    markers = [(r, c, grid[r][c]) for r, c in corners if grid[r][c] in {1, 2, 3, 4}]
    if len(markers) != 1:
        raise ValueError(f"expected one direction marker, found {markers}")
    mr, mc, marker = markers[0]
    dr, dc = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}[marker]

    out = deepcopy(grid)
    blockers = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 5) or (r, c) == (mr, mc):
                continue
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w:
                if (rr, cc) in blockers:
                    break
                out[rr][cc] = color
                rr += dr
                cc += dc
    return out
