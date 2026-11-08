"""Standalone visible-example solve. Earlier rule exposure is disclosed in notes."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('expected a nonempty rectangular grid')
    height, width = len(grid), len(grid[0])
    square = [(r, c) for r in range(height) for c in range(width) if grid[r][c] == 8]
    if not square:
        raise ValueError('cyan source square is missing')
    top, bottom = min(r for r, _ in square), max(r for r, _ in square)
    left, right = min(c for _, c in square), max(c for _, c in square)
    output = [row[:] for row in grid]

    def inside(r, c):
        return 0 <= r < height and 0 <= c < width

    # The straight red family points outwards from the four square corners.
    for r0, c0, vr, vc in ((top,left,-1,-1), (top,right,-1,1),
                            (bottom,left,1,-1), (bottom,right,1,1)):
        r, c = r0 + vr, c0 + vc
        while inside(r, c):
            if grid[r][c] == 5 or (grid[r][c-vc] == 5 and grid[r-vr][c] == 5):
                break
            output[r][c] = 2
            r, c = r+vr, c+vc

    # Yellow corners are paired with the next outward direction clockwise.
    for r0, c0, vr, vc in ((top,left,-1,1), (top,right,1,1),
                            (bottom,right,1,-1), (bottom,left,-1,-1)):
        r, c = r0 + vr, c0 + vc
        if not inside(r, c) or grid[r][c] == 5:
            continue
        output[r][c] = 4
        vertical_first = vr != vc
        while True:
            nr, nc = r+vr, c+vc
            if not inside(nr, nc):
                break
            step = (nr, c) if vertical_first else (r, nc)
            sr, sc = step
            if not inside(sr, sc) or grid[sr][sc] == 5:
                break
            output[sr][sc] = 4
            if grid[nr][nc] == 5:
                break
            output[nr][nc] = 4
            r, c = nr, nc
            vertical_first = not vertical_first
    return output
