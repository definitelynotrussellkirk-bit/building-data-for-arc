"""Visible-example hypothesis: order monochrome components by pixel count."""
def solve(grid):
    h, w = len(grid), len(grid[0])
    visited = set()
    objects = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r,c) in visited:
                continue
            cells, stack = [], [(r,c)]
            visited.add((r,c))
            while stack:
                y,x = stack.pop()
                cells.append((y,x))
                for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
                    yy,xx = y+dy,x+dx
                    if 0 <= yy < h and 0 <= xx < w and (yy,xx) not in visited and grid[yy][xx] == color:
                        visited.add((yy,xx)); stack.append((yy,xx))
            y0=min(y for y,x in cells); x0=min(x for y,x in cells)
            points=[(y-y0,x-x0) for y,x in cells]
            oh=max(y for y,x in points)+1; ow=max(x for y,x in points)+1
            objects.append((len(cells),color,points,oh,ow))
    if not objects:
        return [[0]]
    objects.sort(key=lambda obj: obj[0])
    out=[[0]*(sum(obj[4] for obj in objects)+len(objects)-1) for _ in range(max(obj[3] for obj in objects))]
    offset=0
    for _,color,points,oh,ow in objects:
        for y,x in points: out[y][offset+x]=color
        offset += ow+1
    return out
