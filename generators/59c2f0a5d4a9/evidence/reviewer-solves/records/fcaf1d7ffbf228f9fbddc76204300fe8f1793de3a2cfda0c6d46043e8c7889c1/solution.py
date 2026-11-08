"""Solve from the supplied visible demonstrations only."""
from collections import deque


def solve(grid):
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 1 or (r, c) in seen:
                continue
            region = []
            todo = deque([(r, c)])
            seen.add((r, c))
            boundary = False
            marked = False
            while todo:
                y, x = todo.popleft()
                region.append((y, x))
                boundary |= y in (0, h - 1) or x in (0, w - 1)
                marked |= grid[y][x] == 2
                for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
                    if (0 <= yy < h and 0 <= xx < w
                            and grid[yy][xx] != 1 and (yy, xx) not in seen):
                        seen.add((yy, xx))
                        todo.append((yy, xx))
            if marked and not boundary:
                for y, x in region:
                    out[y][x] = 4
    return out
