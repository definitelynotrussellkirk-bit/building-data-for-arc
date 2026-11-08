def solve(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            component, todo = [], [(r, c)]
            seen.add((r, c))
            while todo:
                y, x = todo.pop()
                component.append((y, x))
                for yy, xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if 0 <= yy < h and 0 <= xx < w and grid[yy][xx] == 5 and (yy,xx) not in seen:
                        seen.add((yy,xx))
                        todo.append((yy,xx))
            if len(component) == 2 and component[0][0] == component[1][0]:
                for y, x in component:
                    out[y][x] = 8
    return out
