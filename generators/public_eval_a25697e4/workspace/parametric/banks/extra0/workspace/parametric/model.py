"""Geometric key/lock inference and deterministic, setting-blind scene construction.

This module never reads ARC labels. Racket independently verifies claimed outputs.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import random

Grid = list[list[int]]
MODES = ('exchange', 'preserve')

def validate_grid(g: Grid) -> None:
    if not isinstance(g, list) or not 1 <= len(g) <= 30 or not isinstance(g[0], list) or not 1 <= len(g[0]) <= 30:
        raise ValueError('expected a nonempty grid no larger than 30x30')
    if any(not isinstance(row,list) or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('grid must be rectangular with exact integer colors 0..9')

def components(g: Grid, bg: int) -> list[set[tuple[int,int]]]:
    todo={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg}
    groups=[]
    while todo:
        p=min(todo); todo.remove(p); group={p}; stack=[p]
        while stack:
            r,c=stack.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    q=(r+dr,c+dc)
                    if q in todo:
                        todo.remove(q);group.add(q);stack.append(q)
        groups.append(group)
    return groups

def bbox(cells):
    if not cells:
        raise ValueError('empty shape')
    return min(p[0] for p in cells),min(p[1] for p in cells),max(p[0] for p in cells),max(p[1] for p in cells)

def transform(cells, turns: int, reflected: bool):
    out=[]
    for r,c,v in cells:
        if reflected:
            c=-c
        for _ in range(turns):
            r,c=c,-r
        out.append((r,c,v))
    return out

def infer(g: Grid) -> dict:
    """Infer the unique full-key assignment, rigid pose and reflection parity."""
    validate_grid(g)
    h,w=len(g),len(g[0]); counts=Counter(v for row in g for v in row)
    ranked=counts.most_common()
    if len(ranked)<2 or ranked[0][1]==ranked[1][1]:
        raise ValueError('background must be uniquely modal')
    bg=ranked[0][0]; keys=[]; groups=defaultdict(set)
    for cells in components(g,bg):
        colors={g[r][c] for r,c in cells}
        if len(colors)==2:
            if any(r in (0,h-1) or c in (0,w-1) for r,c in cells):
                raise ValueError('detached keys must be interior')
            keys.append([(r,c,g[r][c]) for r,c in sorted(cells)])
        elif len(colors)==1:
            sides=[s for s,pred in enumerate((lambda r,c:r==0,lambda r,c:c==w-1,lambda r,c:r==h-1,lambda r,c:c==0)) if any(pred(r,c) for r,c in cells)]
            if len(sides)!=1:
                raise ValueError('each lock fragment must touch exactly one border')
            groups[(sides[0],next(iter(colors)))].update(cells)
        else:
            raise ValueError('keys must contain exactly two colors')
    if not keys or len(groups)!=len(keys):
        raise ValueError('one detached key is required for every border lock')
    stationary=[[bg]*w for _ in range(h)]; locks=[]
    for (side,color),cells in sorted(groups.items()):
        r0,c0,r1,c1=bbox(cells)
        holes={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}-cells
        if not holes:
            raise ValueError('lock must have a cavity')
        locks.append({'side':side,'color':color,'cells':cells,'holes':holes})
        for r,c in cells:
            stationary[r][c]=color
    docks=[]
    for lock in locks:
        hr,hc,_,_=bbox(lock['holes']); candidates=[]
        for ki,key in enumerate(keys):
            colors=sorted({v for r,c,v in key})
            for reflected in (False,True):
                for turns in range(4):
                    t=transform(key,turns,reflected)
                    for plug in colors:
                        tip={(r,c) for r,c,v in t if v==plug}
                        pr,pc,_,_=bbox(tip); dr,dc=hr-pr,hc-pc
                        if {(r+dr,c+dc) for r,c in tip}!=lock['holes']:
                            continue
                        placed=[(r+dr,c+dc,v) for r,c,v in t]
                        if not all(0<=r<h and 0<=c<w and stationary[r][c]==bg for r,c,v in placed):
                            continue
                        candidates.append(dict(key_index=ki,turns=turns,reflected=reflected,
                            translation=[dr,dc],plug_color=plug,colors=colors,placed=placed))
        if len(candidates)!=1:
            raise ValueError(f'lock requires a unique docking pose, found {len(candidates)}')
        docks.append(candidates[0])
    if len({d['key_index'] for d in docks})!=len(keys):
        raise ValueError('docking must be one-to-one')
    occupied=set()
    for d in docks:
        ps={(r,c) for r,c,v in d['placed']}
        if occupied & ps:
            raise ValueError('docked keys collide')
        occupied |= ps
    return dict(background=bg,stationary=stationary,keys=keys,locks=locks,docks=docks)

def render(state: dict, mode: str, rival: str | None = None) -> Grid:
    if mode not in MODES:
        raise ValueError('unknown reflection color setting')
    out=deepcopy(state['stationary'])
    # Racket discovers monochrome components in row-major order, not by side.
    first=min(range(len(state['locks'])),key=lambda i:min(state['locks'][i]['cells']))
    docks=[state['docks'][first]] if rival=='first_lock_only' else state['docks']
    for d in docks:
        reflected=d['reflected']
        if rival=='rotation_only' and reflected:
            continue
        if rival=='always_exchange':
            exchange=True
        elif rival=='never_exchange':
            exchange=False
        elif rival=='opposite_handedness':
            exchange=not reflected
        else:
            exchange=mode=='exchange' and reflected
        for r,c,v in d['placed']:
            if rival=='plug_only' and v!=d['plug_color']:
                continue
            out[r][c] = d['colors'][1-d['colors'].index(v)] if exchange else v
    return out

def solve(g: Grid, mode: str = 'exchange', rival: str | None = None) -> Grid:
    if rival=='identity':
        validate_grid(g); return deepcopy(g)
    return render(infer(g),mode,rival)

def _rng(seed:int, tag:str) -> random.Random:
    if type(seed) is not int:
        raise ValueError('seed must be an exact integer')
    return random.Random(int.from_bytes(hashlib.sha256(f'a25697e4/v1/{seed}/{tag}'.encode()).digest(),'big'))

def _rotate_grid(g: Grid, n:int) -> Grid:
    for _ in range(n):
        g=[list(row) for row in zip(*g[::-1])]
    return g

def _draw_scene(rng: random.Random, h:int, w:int, nlocks:int, reflected:list[bool], stress:bool) -> Grid:
    bg=rng.randrange(10); palette=[v for v in range(10) if v!=bg]
    grid=[[bg]*w for _ in range(h)]; docked=[]
    for j in range(nlocks):
        lh = 9 if stress else rng.randint(4,6)
        lw = 7 if stress else rng.randint(3,5)
        offset=1+rng.randrange(2) if j==0 else h-lh-2
        # A right-open cavity with unequal runs is generally chiral. Exact
        # uniqueness is verified below, not assumed from this construction.
        widths=[0]+[rng.randint(1,lw-1) for _ in range(lh-2)]+[0]
        widths[1]=1; widths[-2]=lw
        lockcolor=rng.choice(palette)
        ca,cb=rng.sample([v for v in palette if v!=lockcolor],2)
        tip={(rr,cc) for rr in range(lh) for cc in range(lw-widths[rr],lw)}
        anchor=rng.randrange(1,lh-1); span=6 if stress else rng.randint(3,5)
        tail=(1 if anchor<lh//2 else -1)*rng.randint(1,3)
        handle={(anchor,lw+i) for i in range(span)}
        handle |= {(anchor+i*(1 if tail>0 else -1),lw+span-1) for i in range(1,abs(tail)+1)}
        handle.add((anchor+tail,lw+span))
        def locate(rr,cc):
            return offset+rr, cc if j==0 else w-1-cc
        for rr in range(lh):
            for cc in range(lw):
                if (rr,cc) not in tip:
                    r,c=locate(rr,cc);grid[r][c]=lockcolor
        key=[(*locate(r,c),ca) for r,c in sorted(tip)]+[(*locate(r,c),cb) for r,c in sorted(handle)]
        if not all(0<=r<h and 0<=c<w for r,c,v in key):
            raise ValueError('docked key outside canvas')
        docked.append(key)
    for j,key in enumerate(docked):
        shaped=transform(key,rng.randrange(4),reflected[j])
        r0,c0,r1,c1=bbox(shaped); shaped=[(r-r0,c-c0,v) for r,c,v in shaped]
        kh,kw=r1-r0+1,c1-c0+1
        candidates=[(r,c) for r in range(1,h-kh) for c in range(1,w-kw)]
        rng.shuffle(candidates)
        for sr,sc in candidates:
            if all(grid[sr+r+dr][sc+c+dc]==bg for r,c,v in shaped for dr in (-1,0,1) for dc in (-1,0,1)):
                for r,c,v in shaped:grid[sr+r][sc+c]=v
                break
        else:
            raise ValueError('source placement exhausted')
    grid=_rotate_grid(grid,rng.randrange(4))
    state=infer(grid)
    if sorted(d['reflected'] for d in state['docks'])!=sorted(reflected):
        raise ValueError('unexpected handedness')
    if stress and sum(v!=bg for row in grid for v in row)<120:
        raise ValueError('stress content below floor')
    return grid

def sample_input(seed:int,index:int, *, query:bool=False) -> Grid:
    if type(index) is not int or index<0:
        raise ValueError('index must be a nonnegative exact integer')
    if type(query) is not bool:
        raise ValueError('query flag must be boolean')
    rng=_rng(seed,f'{"query" if query else "demo"}/{index}')
    if query:
        profiles=[(22,26,1),(25,28,2),(28,28,2),(30,30,2)]
        h,w,n=profiles[index%4]; flags=[bool((index+j)%2) for j in range(n)]
        stress=index%4==3
    else:
        profiles=[(19,23,1),(23,25,2),(21,26,1),(26,24,2),(27,27,2),(24,29,2)]
        h,w,n=profiles[index%6]; flags=[True] if index%6==0 else [bool((index+j)%2) for j in range(n)]
        stress=False
    for _ in range(96):
        try:
            return _draw_scene(rng,h,w,n,flags,stress)
        except ValueError:
            pass
    raise RuntimeError('bounded scene construction exhausted; no silent seed substitution')

def query_order(seed:int) -> list[int]:
    order=list(range(4));_rng(seed,'presentation').shuffle(order);return order
