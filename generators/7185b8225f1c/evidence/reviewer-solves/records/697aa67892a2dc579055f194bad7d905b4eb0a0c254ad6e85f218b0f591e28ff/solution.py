"""Visible-example hypothesis: outline non-isolated red pixels in green."""
def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2:
                continue
            adjacent = any(0 <= r+dr < h and 0 <= c+dc < w
                           and grid[r+dr][c+dc] == 2
                           for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)))
            if adjacent:
                for rr in range(max(0,r-1), min(h,r+2)):
                    for cc in range(max(0,c-1), min(w,c+2)):
                        if grid[rr][cc] == 0:
                            out[rr][cc] = 3
    return out
