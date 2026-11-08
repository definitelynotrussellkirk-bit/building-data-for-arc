"""Legend-set panel erasure, with a sequential survivor-size variant.

The canonical semantic inference is positional-invariant set inclusion, not an
image lookup. The sampler uses disjoint rectangular panels; the solver also
accepts connected nonrectangular black-backed panels.
"""
from collections import Counter
import random


def validate(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
        type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30 or
        any(type(row) is not list or len(row) != len(grid[0]) or
            any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError('rectangular 1..30 exact-integer color grid required')


def components(cells):
    todo=set(cells); result=[]
    while todo:
        start=min(todo); todo.remove(start); comp={start}; stack=[start]
        while stack:
            r,c=stack.pop()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in todo:
                    todo.remove(q);comp.add(q);stack.append(q)
        result.append(sorted(comp))
    return result


def analyze(g):
    validate(g)
    bg=7  # Orange is structural; large black panels may be the modal color.
    frame=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==3]
    if bg==3 or not frame:raise ValueError('a green L legend is required')
    r0=min(r for r,c in frame);r1=max(r for r,c in frame)
    c0=min(c for r,c in frame);c1=max(c for r,c in frame)
    keys={g[r][c] for r in range(r0,r1+1) for c in range(c0,c1+1)}-{bg,0,3}
    if not keys:raise ValueError('legend must contain at least one color')
    ps=components((r,c) for r,row in enumerate(g) for c,v in enumerate(row)
                  if v!=bg and not(r0<=r<=r1 and c0<=c<=c1))
    ps=[p for p in ps if any(g[r][c]==0 for r,c in p)]
    return bg,keys,ps


def solve(g,finish='erase',*,rival=None):
    if finish not in ('erase','largest_survivor'):raise ValueError('unknown finish')
    bg,keys,panels=analyze(g);out=[row[:] for row in g]
    good=[]
    for p in panels:
        cols={g[r][c] for r,c in p}-{0}
        hit=keys<=cols
        if rival=='any_key':hit=bool(keys&cols)
        elif rival=='exact_set':hit=keys==cols
        elif rival=='invert':hit=not hit
        good.append(hit)
    if rival=='first_match':
        first=next((i for i,x in enumerate(good) if x),-1);good=[i==first for i in range(len(good))]
    for p,remove in zip(panels,good):
        if remove:
            for r,c in p:out[r][c]=bg
    survivors=[p for p,removed in zip(panels,good) if not removed]
    if finish=='largest_survivor' and survivors:
        selected=[max(survivors,key=len)]
        if rival=='source_rank':selected=[max(panels,key=len)]
        elif rival=='smallest':selected=[min(survivors,key=len)]
        elif rival=='first_survivor':selected=[survivors[0]]
        elif rival=='last_survivor':selected=[survivors[-1]]
        elif rival=='all_survivors':selected=survivors
        elif rival=='no_finish':selected=[]
        for p in selected:
            for r,c in p:
                if out[r][c]==0:out[r][c]=3
    return out


def rivals(finish):
    return ['any_key','exact_set','invert','first_match']+(
        ['source_rank','smallest','first_survivor','last_survivor','all_survivors','no_finish']
        if finish=='largest_survivor' else [])


def rotate(g,n):
    for _ in range(n%4):g=[list(row) for row in zip(*g[::-1])]
    return g


def scene(seed,index,size,rotation=None):
    rng=random.Random((seed+1)*1000003+index*7907)
    g=[[7]*size for _ in range(size)]
    palette=[1,2,4,5,6,8,9];rng.shuffle(palette)
    k=2+index%3;keys=palette[:k];extra=palette[k]
    for r in range(4):g[r][3]=3
    for c in range(4):g[3][c]=3
    places=[(r,c) for r in range(3) for c in range(3)];rng.shuffle(places)
    for (r,c),color in zip(places,keys+([keys[0]] if index%2 else [])):g[r][c]=color
    half=size//2; topw=(size-8)//2; topheight=half-2
    slots=[(1,6,topheight,topw),(1,7+topw,topheight,size-8-topw),
           (half+1,1,size-half-2,half-2),(half+1,half+1,size-half-2,size-half-2)]
    # One large erased superset, a smaller erased exact-set, and two retained
    # partial matches. The largest source panel is always erased.
    big=2+index%2; other=5-big
    dims={big:(slots[big][2],slots[big][3]),other:(3,3),
          0:(max(4,topheight-1),topw),1:(3,topw)}
    # Largest retained panel alternates slots, not a fixed reading-order rule.
    if index%2:dims[0],dims[1]=dims[1],dims[0]
    larger=0 if dims[0][0]*dims[0][1]>dims[1][0]*dims[1][1] else 1
    for i,(r,c,_,_) in enumerate(slots):
        hh,ww=dims[i]
        for rr in range(r,r+hh):
            for cc in range(c,c+ww):g[rr][cc]=0
        cs=(keys+[extra,keys[0]]) if i==big else keys if i==other else keys[:-1]+[extra] if i==larger else keys[1:]+[extra]
        cells=[(rr,cc) for rr in range(r,r+hh) for cc in range(c,c+ww)];rng.shuffle(cells)
        for (rr,cc),co in zip(cells,cs):g[rr][cc]=co
    rot=(seed%4 if index%2==0 else (seed+2)%4) if rotation is None else rotation
    return rotate(g,rot)


def bank(seed):
    # Resample the bounded lesson jointly only when a declared shortcut remains.
    # Selection uses demonstrations alone and is independent of requested counts.
    for attempt in range(64):
        s=seed+attempt*104729
        demos=[scene(s,i,16+2*(i%3)) for i in range(6)]
        if all(any(solve(g,mode,rival=r)!=solve(g,mode) for g in demos[:2])
               for mode in ('erase','largest_survivor') for r in rivals(mode)):
            queries=[scene(s,20+i,n) for i,n in enumerate((16,20,24,30))]
            random.Random(seed^0xD59B0160).shuffle(queries)
            return demos,queries
    raise ValueError('bounded teaching search found no distinguishing pair')
