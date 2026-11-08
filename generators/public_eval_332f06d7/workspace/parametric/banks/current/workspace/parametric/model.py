"""Rigid-block configuration-space routing, independent Python label claims."""
from __future__ import annotations
from collections import deque
DIRECTIONS=((-1,0),(0,-1),(0,1),(1,0))

def validate(grid):
    if type(grid) is not list or not grid or len(grid)>30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('nonempty grid of at most 30x30 required')
    w=len(grid[0])
    if any(type(row) is not list or len(row)!=w or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('rectangular exact integer colors required')

def flood(starts,allowed):
    distance={p:0 for p in starts};queue=deque(starts)
    while queue:
        r,c=queue.popleft()
        for dr,dc in DIRECTIONS:
            q=(r+dr,c+dc)
            if q in allowed and q not in distance:distance[q]=distance[(r,c)]+1;queue.append(q)
    return distance

def backtrack(start,terminal,reachable):
    path=[terminal]
    while path[-1]!=start:
        r,c=path[-1];previous=[(r+dr,c+dc) for dr,dc in DIRECTIONS if reachable.get((r+dr,c+dc))==reachable[(r,c)]-1]
        if not previous:raise ValueError('broken route distance field')
        path.append(min(previous))
    return list(reversed(path))

def analyze(grid):
    validate(grid);h,w=len(grid),len(grid[0])
    zeros={(r,c)for r in range(h)for c in range(w)if grid[r][c]==0}
    goals={(r,c)for r in range(h)for c in range(w)if grid[r][c]==2}
    if not zeros or not goals:raise ValueError('black block and red goal required')
    top=min(r for r,c in zeros);left=min(c for r,c in zeros)
    sh=max(r for r,c in zeros)-top+1;sw=max(c for r,c in zeros)-left+1
    if len(zeros)!=sh*sw:raise ValueError('black block must be a solid rectangle')
    start=(top,left)
    cells={(r,c)for r in range(h)for c in range(w)if grid[r][c] in (0,1,2)}
    distances=flood(sorted(goals),cells)
    if start not in distances:raise ValueError('goal must share a walkable-cell component with the block')
    legal={(r,c)for r in range(h-sh+1)for c in range(w-sw+1)
           if all((r+a,c+b)in cells for a in range(sh)for b in range(sw))}
    reachable=flood([start],legal)
    scores={p:sum(distances.get((p[0]+a,p[1]+b),h*w+1)for a in range(sh)for b in range(sw))for p in reachable}
    terminal=min(reachable,key=lambda p:(scores[p],p))
    return {'shape':(sh,sw),'start':start,'goals':sorted(goals),'walkable':cells,
            'goal_distances':distances,'legal':legal,'reachable':reachable,'scores':scores,
            'terminal':terminal,'ties':sorted(p for p in reachable if scores[p]==scores[terminal]),
            'route':backtrack(start,terminal,reachable)}

def render(grid,data,travel='terminal'):
    if travel not in ('terminal','halfway'):raise ValueError('unknown travel setting')
    route=data['route'];destination=route[-1] if travel=='terminal' else route[len(route)//2]
    r,c=destination;sh,sw=data['shape']
    if not (0<=r<=len(grid)-sh and 0<=c<=len(grid[0])-sw):raise ValueError('destination outside canvas')
    out=[[1 if v==0 else v for v in row]for row in grid]
    for a in range(sh):
        for b in range(sw):out[r+a][c+b]=0
    return out

def solve(grid,travel='terminal'):
    return render(grid,analyze(grid),travel)
