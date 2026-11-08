"""Color-table enclosed-hole family for public parent dbff022c."""
from __future__ import annotations
from collections import Counter
import hashlib,random
from typing import Any
SETTINGS=('fill_only','highlight_dominant_fill')
HIGHLIGHT=9
CARDINAL=((-1,0),(1,0),(0,-1),(0,1))

def checked_grid(grid:Any)->list[list[int]]:
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30 or
        any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected rectangular exact integer-color grid with dimensions 1..30')
    return grid

def bbox(cells):
    return min(r for r,c in cells),max(r for r,c in cells),min(c for r,c in cells),max(c for r,c in cells)

def components(grid,background=0,diagonal=False,mono=True):
    unseen={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=background};out=[]
    while unseen:
        p=min(unseen);unseen.remove(p);queue=[p];cells=[]
        for r,c in queue:
            cells.append((r,c))
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if not (dr or dc) or (not diagonal and dr and dc):continue
                    q=(r+dr,c+dc)
                    if q in unseen and (not mono or grid[q[0]][q[1]]==grid[r][c]):
                        unseen.remove(q);queue.append(q)
        out.append(cells)
    return out

def analyze(grid):
    g=checked_grid(grid);objs=components(g,0,True,False)
    candidates=[]
    for o in objs:
        a,b,c,d=bbox(o);colors={g[r][col] for r,col in o}
        if len(colors)>=4 and len(o)==(b-a+1)*(d-c+1) and (b-a+1==2 or d-c+1==2):candidates.append(o)
    if len(candidates)!=1:raise ValueError('Expected one filled 2xN or Nx2 color correspondence table')
    table=candidates[0];a,b,c,d=bbox(table);p=[row[c:d+1] for row in g[a:b+1]]
    table_set=set(table);outside_colors={g[r][col] for r in range(len(g)) for col in range(len(g[0])) if (r,col) not in table_set and g[r][col]!=0}
    mappings=[]
    if len(p)==2:mappings.extend([dict(zip(p[0],p[1])),dict(zip(p[1],p[0]))])
    if len(p[0])==2:
        left=[row[0] for row in p];right=[row[1] for row in p]
        mappings.extend([dict(zip(left,right)),dict(zip(right,left))])
    mapping=max(mappings,key=lambda m:len(set(m)&outside_colors))
    return {'table':table,'bbox':(a,b,c,d),'mapping':mapping,'outside_colors':outside_colors}

def fill(grid):
    g=checked_grid(grid);info=analyze(g);mapping=info['mapping'];out=[row[:] for row in g]
    zero_mask=[[1 if v==0 else 0 for v in row] for row in g]
    filled=[]
    for hole in components(zero_mask,0,False,True):
        if any(r in (0,len(g)-1) or c in (0,len(g[0])-1) for r,c in hole):continue
        border={g[r+dr][c+dc] for r,c in hole for dr,dc in CARDINAL if g[r+dr][c+dc]!=0}
        if len(border)==1 and next(iter(border)) in mapping:
            value=mapping[next(iter(border))]
            for r,c in hole:out[r][c]=value;filled.append((r,c,value,next(iter(border))))
    return out,filled,info

def solve(grid,finish_rule='fill_only'):
    if finish_rule not in SETTINGS:raise ValueError('Unknown finish_rule')
    out,filled,_=fill(grid)
    if finish_rule=='highlight_dominant_fill':
        counts=Counter(v for r,c,v,k in filled)
        if not counts:raise ValueError('Expected at least one mapped enclosed hole')
        ordered=counts.most_common()
        if len(ordered)>1 and ordered[0][1]==ordered[1][1]:raise ValueError('Dominant filled color must be unique')
        selected=ordered[0][0]
        for r,c,v,k in filled:
            if v==selected:out[r][c]=HIGHLIGHT
    return out

def causal_intermediate(grid):
    completed,filled,info=fill(grid);fill_counts=Counter(v for r,c,v,k in filled);frame_counts=Counter()
    table=set(info['table'])
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if (r,c) not in table and v in info['mapping']:frame_counts[v]+=1
    dominant=max(fill_counts,key=fill_counts.get)
    raw_key=max(frame_counts,key=frame_counts.get)
    return {'fill_counts':dict(fill_counts),'frame_counts':dict(frame_counts),'dominant_fill':dominant,'raw_frequency_fill':info['mapping'][raw_key]}

def validate_request(seed,demos,queries):
    for value,lo,hi,name in ((seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')):
        if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')

def _rng(seed,index,query):
    raw=hashlib.sha256(f'dbff022c-v1|{seed}|{query}|{index}'.encode()).digest();return random.Random(int.from_bytes(raw,'big'))

def _frame(g,top,left,height,width,color):
    for c in range(left,left+width):g[top][c]=g[top+height-1][c]=color
    for r in range(top,top+height):g[r][left]=g[r][left+width-1]=color

def scene(seed,index,*,query=False):
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0:raise ValueError('Invalid seed/index')
    rng=_rng(seed,index,query)
    if query and index%4==3:h=w=30
    else:
        h=22+((3*index+(4 if query else 0)+rng.randrange(3))%6)
        w=22+((5*index+(2 if query else 0)+rng.randrange(3))%6)
    palette=rng.sample(range(1,9),7)
    # Keep the dominant-fill key numerically later than another mapped key.
    # Otherwise a minimum-key/"first mapping" shortcut can accidentally fit a
    # short lesson whenever random palette order puts key 0 first.
    ordered_keys=sorted(palette[:3]);keys=[ordered_keys[2],ordered_keys[0],ordered_keys[1]]
    values=palette[3:6];unmapped=palette[6]
    g=[[0]*w for _ in range(h)]
    vertical=(index+(1 if query else 0)+seed)%2==1
    if vertical:
        for i,(k,v) in enumerate(zip(keys,values)):g[i][0]=k;g[i][1]=v
    else:
        for i,(k,v) in enumerate(zip(keys,values)):g[0][i]=k;g[1][i]=v
    # k0: two medium holes, each area 12, whose total area 24 is dominant.
    # This forces aggregation by mapped output color rather than selection of
    # the largest individual hole.
    _frame(g,3,3,5,6,keys[0]);_frame(g,10,3,5,6,keys[0])
    # k1: three thin frames.  Their raw perimeter total 52 exceeds k0's 36
    # and their hole count 3 exceeds k0's 2, while combined enclosed area 17
    # remains smaller than k0's 24.  This refutes both raw-frequency and
    # most-holes shortcuts without changing the correct area winner.
    _frame(g,3,w-9,3,9,keys[1]);_frame(g,15,3,3,5,keys[1]);_frame(g,h-3,0,3,9,keys[1])
    # k2 owns the largest single hole (area 20) but loses after k0's two holes
    # are aggregated.  The unmapped decoy remains unchanged.
    _frame(g,7,w-9,6,7,keys[2]);_frame(g,h-8,w-7,5,6,unmapped)
    completed,filled,info=fill(g);mid=causal_intermediate(g)
    if mid['dominant_fill']!=values[0] or mid['raw_frequency_fill']!=values[1]:raise RuntimeError('Scene failed causal separation')
    if query and index%4==3:
        if sum(v!=0 for row in g for v in row)<70:raise RuntimeError('30x30 stress too sparse')
        if not all(any(g[r][c] for r,c in edge) for edge in (
            [(0,c) for c in range(w)],[(h-1,c) for c in range(w)],[(r,0) for r in range(h)],[(r,w-1) for r in range(h)])):raise RuntimeError('30x30 stress must touch all boundaries')
    return g
