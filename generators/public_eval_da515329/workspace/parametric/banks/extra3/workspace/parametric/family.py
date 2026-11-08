"""General four-arm spiral family for public parent da515329."""
from __future__ import annotations
from collections import Counter
import hashlib, random
from typing import Any

DIRECTIONS=((-1,0),(0,1),(1,0),(0,-1))
NEIGHBORS=tuple((dr,dc) for dr in (-1,0,1) for dc in (-1,0,1))
SETTINGS=('spiral_only','highlight_longest')
LINE_COLORS=(1,3,4,5,6,7,8,9)
HIGHLIGHT=2

def checked_grid(grid: Any)->list[list[int]]:
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or
        not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0]) or
        any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected rectangular exact integer-color grid with dimensions 1..30')
    return grid

def parse_cross(grid:list[list[int]]):
    g=checked_grid(grid);counts=Counter(v for row in g for v in row)
    if len(counts)!=2 or 0 not in counts:raise ValueError('Expected black background and one line color')
    color=next(v for v in counts if v!=0)
    points={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==color}
    top,bottom=min(r for r,c in points),max(r for r,c in points)
    left,right=min(c for r,c in points),max(c for r,c in points)
    center=((top+bottom)//2,(left+right)//2);length=(bottom-top)//2
    expected={(center[0]+dr*s,center[1]+dc*s) for dr,dc in DIRECTIONS for s in range(1,length+1)}
    if ((bottom-top)%2 or right-left!=2*length or length<1 or points!=expected):
        raise ValueError('Expected a four-arm cross with a blank center')
    return color,center,length

def rotations(point):
    row,col=point
    for _ in range(4):
        yield row,col
        row,col=col,-row

def complete_spiral(grid:list[list[int]])->list[list[int]]:
    g=checked_grid(grid);color,(center_row,center_col),length=parse_cross(g)
    height,width=len(g),len(g[0])
    paths=[[(dr*s,dc*s) for s in range(1,length+1)] for dr,dc in DIRECTIONS]
    occupied={point for path in paths for point in path}
    head=paths[0][-1];previous=paths[0][-2:];heading=0
    out=[row[:] for row in g];turns_outside=0
    for tick in range(100000):
        allowed=set(previous)
        for direction in ((heading+1)%4,heading,(heading-1)%4):
            dr,dc=DIRECTIONS[direction];candidate=(head[0]+dr,head[1]+dc)
            if all((candidate[0]+nr,candidate[1]+nc) not in occupied or
                   (candidate[0]+nr,candidate[1]+nc) in allowed for nr,nc in NEIGHBORS):
                break
        else:raise ValueError(f'No legal continuation at tick {tick}')
        proposals=tuple(rotations(candidate))
        if any(max(abs(a[0]-b[0]),abs(a[1]-b[1]))<=1 for i,a in enumerate(proposals) for b in proposals[i+1:]):
            raise ValueError('Simultaneous path collision')
        visible=False
        for row,col in proposals:
            row+=center_row;col+=center_col
            if 0<=row<height and 0<=col<width:
                out[row][col]=color;visible=True
        if visible:turns_outside=0
        elif direction==(heading+1)%4:turns_outside+=1
        elif direction!=heading:turns_outside-=1
        if not visible and turns_outside>=4:return out
        occupied.update(proposals);head,heading=candidate,direction;previous=(previous+[candidate])[-2:]
    raise RuntimeError('Spiral did not leave the finite canvas')

def components_of(grid:list[list[int]],color:int):
    unseen={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color};result=[]
    while unseen:
        seed=min(unseen);unseen.remove(seed);stack=[seed];cells=[]
        while stack:
            r,c=stack.pop();cells.append((r,c))
            for dr,dc in DIRECTIONS:
                q=(r+dr,c+dc)
                if q in unseen:unseen.remove(q);stack.append(q)
        result.append(sorted(cells))
    return result

def solve(grid:list[list[int]],finish_rule:str='spiral_only')->list[list[int]]:
    if finish_rule not in SETTINGS:raise ValueError('Unknown finish_rule')
    color,_,_=parse_cross(grid);out=complete_spiral(grid)
    if finish_rule=='highlight_longest':
        groups=components_of(out,color)
        if not groups:raise ValueError('Completed spiral has no path components')
        sizes=sorted((len(x) for x in groups),reverse=True)
        if len(sizes)>1 and sizes[0]==sizes[1]:raise ValueError('Longest component must be unique')
        for r,c in max(groups,key=len):out[r][c]=HIGHLIGHT
    return out

def causal_intermediate(grid):
    color,_,_=parse_cross(grid);completed=complete_spiral(grid);groups=components_of(completed,color)
    chosen=max(groups,key=len)
    return {'component_sizes':sorted((len(x) for x in groups),reverse=True),'largest_size':len(chosen),'largest_cells':chosen}

def validate_request(seed:int,demos:int,queries:int):
    for value,lo,hi,name in ((seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')):
        if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')

def _rng(seed,index,query):
    raw=hashlib.sha256(f'da515329-v1|{seed}|{query}|{index}'.encode()).digest()
    return random.Random(int.from_bytes(raw,'big'))

def _cross(h,w,cr,cc,length,color):
    g=[[0]*w for _ in range(h)]
    for dr,dc in DIRECTIONS:
        for step in range(1,length+1):g[cr+dr*step][cc+dc*step]=color
    return g

def scene(seed:int,index:int,*,query:bool=False)->list[list[int]]:
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0:raise ValueError('Invalid seed/index')
    rng=_rng(seed,index,query);color=LINE_COLORS[(seed+3*index+(4 if query else 0))%len(LINE_COLORS)]
    for attempt in range(4000):
        if query and index%4==3:h=w=30
        elif query:
            h=18+((index*5+attempt+rng.randrange(8))%11);w=18+((index*7+attempt+rng.randrange(8))%11)
        else:
            h=14+((index*3+attempt+rng.randrange(8))%13);w=14+((index*5+attempt+rng.randrange(8))%13)
        maxlen=min(4,(h-5)//2,(w-5)//2);length=1+rng.randrange(maxlen)
        cr=rng.randrange(length+2,h-length-2);cc=rng.randrange(length+2,w-length-2)
        g=_cross(h,w,cr,cc,length,color);completed=complete_spiral(g);groups=components_of(completed,color)
        sizes=sorted((len(x) for x in groups),reverse=True)
        if len(sizes)<3 or sizes[0]==sizes[1] or sizes[0]<12:continue
        if query and index%4==3:
            if sum(v!=0 for row in completed for v in row)<220:continue
            if not all(any(completed[r][c] for r,c in edge) for edge in (
                [(0,c) for c in range(w)],[(h-1,c) for c in range(w)],[(r,0) for r in range(h)],[(r,w-1) for r in range(h)])):continue
        return g
    raise RuntimeError('Unable to construct a unique-longest clipped spiral')
