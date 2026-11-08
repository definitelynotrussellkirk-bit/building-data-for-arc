def solve(grid):
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    seen = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            cells = [(r, c)]
            for y, x in cells:
                for yy, xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if 0 <= yy < h and 0 <= xx < w and (yy,xx) not in seen and grid[yy][xx] == color:
                        seen.add((yy,xx))
                        cells.append((yy,xx))
            y0, y1 = min(y for y,x in cells), max(y for y,x in cells)
            x0, x1 = min(x for y,x in cells), max(x for y,x in cells)
            for y in range(y0+1, y1):
                for x in range(x0+1, x1):
                    if (y-y0+x-x0) % 2 == 0:
                        out[y][x] = 0
    return out
