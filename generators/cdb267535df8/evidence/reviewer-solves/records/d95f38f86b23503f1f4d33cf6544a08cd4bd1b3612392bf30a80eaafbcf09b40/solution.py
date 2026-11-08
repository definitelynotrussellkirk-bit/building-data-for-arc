"""Infer wall-aware nearest-color filling from visible demonstrations."""
from collections import deque


def solve(grid):
    if not grid or not grid[0] or any(len(row)!=len(grid[0]) for row in grid):
        raise ValueError('Expected a nonempty rectangular grid')
    h,w=len(grid),len(grid[0])
    colors=sorted({v for row in grid for v in row if v not in (0,5)})
    distances={}
    for color in colors:
        d=[[None]*w for _ in range(h)]
        queue=deque()
        for r,row in enumerate(grid):
            for c,v in enumerate(row):
                if v==color:d[r][c]=0;queue.append((r,c))
        while queue:
            r,c=queue.popleft()
            for a,b in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if 0<=a<h and 0<=b<w and grid[a][b]!=5 and d[a][b] is None:
                    d[a][b]=d[r][c]+1;queue.append((a,b))
        distances[color]=d
    out=[list(row) for row in grid]
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v:continue
            candidates=[(distances[color][r][c],color) for color in colors
                        if distances[color][r][c] is not None]
            if candidates:
                best=min(d for d,_ in candidates)
                winners=[color for d,color in candidates if d==best]
                if len(winners)==1:out[r][c]=winners[0]
    return out
