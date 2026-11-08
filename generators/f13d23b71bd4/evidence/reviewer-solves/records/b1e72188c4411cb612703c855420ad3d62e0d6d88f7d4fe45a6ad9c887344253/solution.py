"""Visible-example hypothesis: lower the largest monochromatic object."""
from collections import Counter


def solve(grid):
    h, w = len(grid), len(grid[0])
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg or (r, c) in seen:
                continue
            color = grid[r][c]
            cells, stack = [], [(r, c)]
            seen.add((r, c))
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for yy, xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if 0 <= yy < h and 0 <= xx < w and (yy,xx) not in seen and grid[yy][xx] == color:
                        seen.add((yy,xx))
                        stack.append((yy,xx))
            objects.append((color, cells))
    result = [row[:] for row in grid]
    if objects:
        color, cells = max(objects, key=lambda obj: len(obj[1]))
        delta = h - 1 - max(r for r, c in cells)
        for r, c in cells:
            result[r][c] = bg
        for r, c in cells:
            result[r+delta][c] = color
    return result
