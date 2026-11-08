from collections import deque


def _components_of_color(grid, color):
    rows, cols = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                cr, cc = q.popleft()
                cells.append((cr, cc))
                for nr, nc in ((cr-1,cc),(cr+1,cc),(cr,cc-1),(cr,cc+1)):
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == color and (nr,nc) not in seen:
                        seen.add((nr,nc)); q.append((nr,nc))
            components.append(cells)
    return components


def solve(grid):
    out = [row[:] for row in grid]
    components = _components_of_color(grid, 5)
    if not components:
        return out
    boxes=[]
    for cells in components:
        rs=[r for r,_ in cells]; cs=[c for _,c in cells]
        boxes.append((min(rs),min(cs),max(rs)-min(rs)+1,max(cs)-min(cs)+1))
    h,w=boxes[0][2:]
    colored=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,5)]
    if not colored:
        return out
    sr=min(r for r,_ in colored); sc=min(c for _,c in colored)
    stencil=[grid[r][sc:sc+w] for r in range(sr,sr+h)]
    for top,left,bh,bw in boxes:
        if (bh,bw)!=(h,w):
            continue
        for dr in range(h):
            for dc in range(w):
                out[top+dr][left+dc]=stencil[dr][dc]
    return out
