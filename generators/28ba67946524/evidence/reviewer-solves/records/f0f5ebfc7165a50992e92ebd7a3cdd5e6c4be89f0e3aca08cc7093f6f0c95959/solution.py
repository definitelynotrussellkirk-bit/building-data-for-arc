"""Visible-example solution: select components two contacts from blue."""
from collections import deque


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid,list) or not grid or not isinstance(grid[0],list) or not grid[0]:
        raise ValueError('expected a nonempty grid')
    h,w=len(grid),len(grid[0])
    if any(not isinstance(row,list) or len(row)!=w for row in grid):
        raise ValueError('expected rectangular rows')
    if any(type(v) is not int or not 0<=v<=9 for row in grid for v in row):
        raise ValueError('expected integer colors 0..9')
    owner={};objects=[];colors=[]
    def near(r,c):
        for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if 0<=rr<h and 0<=cc<w: yield rr,cc
    for r in range(h):
        for c in range(w):
            if grid[r][c]==0 or (r,c) in owner:continue
            i=len(objects);col=grid[r][c];cells=[];pending=[(r,c)];owner[r,c]=i
            while pending:
                rr,cc=pending.pop();cells.append((rr,cc))
                for q in near(rr,cc):
                    if q not in owner and grid[q[0]][q[1]]==col:
                        owner[q]=i;pending.append(q)
            objects.append(cells);colors.append(col)
    starts=[i for i,col in enumerate(colors) if col==1]
    if len(starts)!=1:raise ValueError('expected one blue component')
    adjacency=[set() for _ in objects]
    for (r,c),i in owner.items():
        for q in near(r,c):
            j=owner.get(q)
            if j is not None and i!=j:adjacency[i].add(j)
    distances={starts[0]:0};pending=deque(starts)
    while pending:
        i=pending.popleft()
        for j in adjacency[i]:
            if j not in distances:
                distances[j]=distances[i]+1;pending.append(j)
    out=[[0]*w for _ in range(h)]
    for i,d in distances.items():
        if d==2:
            for r,c in objects[i]:out[r][c]=8
    return out
