"""Independent model of arrow-legend movement inside color-coded enclosures."""
from __future__ import annotations
from collections import Counter

CARDINAL=((-1,0),(0,-1),(0,1),(1,0))
DIRECTIONS=tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c)


def validate_grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
            or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0])
            or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected rectangular 1..30 exact integer color grid')


def components(grid, *, free=False):
    h,w=len(grid),len(grid[0])
    left={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if (v in (0,4) if free else v!=0)}
    out=[]
    while left:
        p=min(left);left.remove(p);todo=[p];cells=[];color=grid[p[0]][p[1]]
        while todo:
            r,c=todo.pop();cells.append((r,c))
            for dr,dc in CARDINAL:
                q=r+dr,c+dc
                if q in left and (free or grid[q[0]][q[1]]==color):left.remove(q);todo.append(q)
        out.append((color,sorted(cells)))
    return out


def legends(grid):
    records=[]
    for color,cells in components(grid):
        if color in (2,4):continue
        top=min(r for r,c in cells);bottom=max(r for r,c in cells)
        left=min(c for r,c in cells);right=max(c for r,c in cells)
        if bottom-top<3 or right-left<3:continue
        edge={(r,c) for r in range(top,bottom+1) for c in range(left,right+1)
              if r in (top,bottom) or c in (left,right)}
        if any(grid[r][c]!=color for r,c in edge):continue
        inner=[(r,c) for r in range(top+1,bottom) for c in range(left+1,right)]
        heads=[(r,c) for r,c in inner if grid[r][c]==2]
        bodies={grid[r][c] for r,c in inner}-{0,2,4,color}
        if not heads or len(bodies)!=1:continue
        body=next(iter(bodies))
        directions=[]
        for dr,dc in DIRECTIONS:
            if all(all(top<r-k*dr<bottom and left<c-k*dc<right and grid[r-k*dr][c-k*dc]==body
                       for k in (1,2)) for r,c in heads):directions.append((dr,dc))
        if len(directions)==1:
            records.append({'color':color,'direction':directions[0],'bbox':(top,left,bottom,right),'body':body})
    return records


def free_run(grid, p, direction):
    h,w=len(grid),len(grid[0]);r,c=p;dr,dc=direction;distance=0
    def free(rr,cc): return 0<=rr<h and 0<=cc<w and grid[rr][cc] in (0,4)
    # A diagonal step sweeps both side cells; do not slip across a wall corner.
    while free(r+dr,c+dc) and free(r+dr,c) and free(r,c+dc):
        r+=dr;c+=dc;distance+=1
    return distance


def analyze(grid):
    validate_grid(grid)
    ls=legends(grid);by_color={l['color']:l for l in ls}
    free=components(grid,free=True);h,w=len(grid),len(grid[0]);particles=[]
    for _,cells in free:
        seeds=[p for p in cells if grid[p[0]][p[1]]==4]
        if not seeds:continue
        counts=Counter()
        for r,c in cells:
            for dr,dc in CARDINAL:
                rr,cc=r+dr,c+dc
                if 0<=rr<h and 0<=cc<w and grid[rr][cc] in by_color:counts[grid[rr][cc]]+=1
        if not counts:raise ValueError('Particle has no enclosing legend-colored wall')
        color=min(counts,key=lambda col:(-counts[col],col))
        direction=by_color[color]['direction']
        for p in seeds:
            particles.append({'position':p,'wall_color':color,'direction':direction,
                              'distance':free_run(grid,p,direction)})
    return {'legends':ls,'particles':sorted(particles,key=lambda p:p['position'])}


def render(grid, particles, mode='to_wall'):
    if mode not in ('to_wall','halfway'):raise ValueError('Unknown motion extent')
    out=[[0 if v==4 else v for v in row] for row in grid]
    for particle in particles:
        r,c=particle['position'];dr,dc=particle['direction'];distance=particle['distance']
        steps=(distance+1)//2 if mode=='halfway' else distance
        out[r+steps*dr][c+steps*dc]=4
    return out


def solve(grid, mode='to_wall'):
    return render(grid,analyze(grid)['particles'],mode)
