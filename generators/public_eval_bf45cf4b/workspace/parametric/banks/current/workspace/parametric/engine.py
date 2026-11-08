"""General stencil/tile product semantics and bounded matched-input construction.

No official grids, labels, or parent files are accessed by this module.
"""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import hashlib
import random

VALUES=('all','largest')
RIVALS=('other_setting','first_component','last_component','smallest_component',
        'fill_stencil_box','flip_stencil','transpose_tile','flat_tile','flip_tile')
N4=((-1,0),(0,-1),(0,1),(1,0))
N8=tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if (r,c)!=(0,0))


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an integer in {low}..{high}; bool is forbidden')
    return value


def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular 1..30 exact-integer color grid')


def components(cells,diagonal=False):
    left=set(cells);out=[]
    while left:
        start=min(left);left.remove(start);q=[start];found={start}
        for r,c in q:
            for dr,dc in (N8 if diagonal else N4):
                p=(r+dr,c+dc)
                if p in left:left.remove(p);found.add(p);q.append(p)
        out.append(sorted(found))
    return out


def bbox(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)


def parse(g):
    grid_check(g);freq=Counter(v for row in g for v in row)
    if sum(n==max(freq.values()) for n in freq.values())!=1:
        raise ValueError('Expected a unique modal background')
    bg=min(freq,key=lambda c:(-freq[c],c))
    groups=components(((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg),True)
    if len(groups)!=2:raise ValueError('Expected two separated 8-connected foreground objects')
    colors=[{g[r][c] for r,c in group} for group in groups]
    mono=[i for i,cs in enumerate(colors) if len(cs)==1]
    if len(mono)!=1:raise ValueError('Exactly one object must be monochrome and the other multicolor')
    mi=mono[0];ti=1-mi
    def crop(group):
        r0,c0,r1,c1=bbox(group)
        return [row[c0:c1+1] for row in g[r0:r1+1]],(r0,c0,r1,c1)
    mask,mb=crop(groups[mi]);tile,tb=crop(groups[ti])
    if len(mask)*len(tile)>30 or len(mask[0])*len(tile[0])>30:
        raise ValueError('Product dimensions exceed 30')
    # Rectangular supports must not contain cells from the other object.
    for group,box in [(groups[ti],mb),(groups[mi],tb)]:
        if any(box[0]<=r<=box[2] and box[1]<=c<=box[3] for r,c in group):
            raise ValueError('Role bounding boxes overlap foreground')
    occupied={(r,c) for r,row in enumerate(mask) for c,v in enumerate(row) if v!=bg}
    regions=components(occupied)
    return dict(background=bg,mask=mask,tile=tile,occupied=occupied,regions=regions,
                mask_bbox=mb,tile_bbox=tb)


def solve(g,value='all',rival=None):
    if value not in VALUES:raise ValueError('Unknown mask rule')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    p=parse(g);bg=p['background'];mask=p['mask'];tile=p['tile'];regions=p['regions']
    if rival=='other_setting':value='largest' if value=='all' else 'all'
    if rival=='first_component':active=regions[0]
    elif rival=='last_component':active=regions[-1]
    elif rival=='smallest_component':active=min(regions,key=len)
    elif value=='largest':active=max(regions,key=len)
    else:active=p['occupied']
    active=set(active)
    if rival=='fill_stencil_box':active={(r,c) for r in range(len(mask)) for c in range(len(mask[0]))}
    if rival=='flip_stencil':active={(r,len(mask[0])-1-c) for r,c in active}
    if rival=='transpose_tile':tile=[list(x) for x in zip(*tile)]
    if rival=='flip_tile':tile=[row[::-1] for row in tile]
    if rival=='flat_tile':
        color=min(v for row in tile for v in row if v!=bg)
        tile=[[color]*len(tile[0]) for _ in tile]
    th,tw=len(tile),len(tile[0])
    return [[tile[r%th][c%tw] if (r//th,c//tw) in active else bg
             for c in range(len(mask[0])*tw)] for r in range(len(mask)*th)]


def self_check(g):
    try:parse(g)
    except (ValueError,TypeError,IndexError) as e:return [str(e)]
    return []


def stream(seed,kind,index=0):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**63-1,'index')
    return random.Random(int.from_bytes(hashlib.sha256(f'bf45cf4b:{seed}:{kind}:{index}'.encode()).digest(),'big'))


def random_mask(rng,stress=False):
    # Eight-connected growth permits diagonal bridges between 4-components.
    for _ in range(512):
        h=w=5 if stress else 0
        if not stress:h,w=rng.randint(3,6),rng.randint(3,6)
        target=rng.randint(max(5,(h+w)//2),min(h*w-2,17))
        cells={(rng.randrange(h),rng.randrange(w))}
        while len(cells)<target:
            frontier=sorted({(r+dr,c+dc) for r,c in cells for dr,dc in N8
                if 0<=r+dr<h and 0<=c+dc<w} - cells)
            cells.add(rng.choice(frontier))
        r0,c0,r1,c1=bbox(cells);cells={(r-r0,c-c0) for r,c in cells}
        h,w=r1-r0+1,c1-c0+1
        regions=components(cells);sizes=sorted(map(len,regions),reverse=True)
        if len(regions)<2 or len(regions)>5 or sizes[0]==sizes[1] or sizes[0]<3:continue
        if stress and (h,w)!=(5,5):continue
        if h<2 or w<2:continue
        return cells,h,w
    raise ValueError('Bounded stencil sampler exhausted')


def make_input(seed,index,kind='ordinary',stress=False):
    rng=stream(seed,kind,index)
    cells,mh,mw=random_mask(rng,stress)
    th,tw=(6,6) if stress else (rng.randint(2,min(5,30//mh)),rng.randint(2,min(5,30//mw)))
    palette=rng.sample(range(10),rng.randint(4,6));bg,mc=palette[:2];ink=palette[2:]
    mask=[[mc if (r,c) in cells else bg for c in range(mw)] for r in range(mh)]
    # Dense connected tiles with interior background holes are valid textures.
    for _ in range(64):
        tile=[[rng.choice(ink) if rng.random()>.12 else bg for _ in range(tw)] for _ in range(th)]
        tile[0][0]=ink[0];tile[-1][-1]=ink[1]
        occupied=[(r,c) for r in range(th) for c in range(tw) if tile[r][c]!=bg]
        if len(components(occupied,True))==1:break
    else:raise ValueError('Bounded tile sampler exhausted')
    if stress:
        h=w=30
        if rng.randrange(2):positions=[(0,0),(30-th,30-tw)]
        else:positions=[(30-mh,30-mw),(0,0)]
    elif rng.randrange(2):
        h=max(mh,th)+rng.randint(5,9);w=mw+tw+rng.randint(5,9)
        gap=rng.randint(2,3);left=rng.randint(1,w-mw-tw-gap-1)
        positions=[(rng.randrange(h-mh+1),left),(rng.randrange(h-th+1),left+mw+gap)]
        if rng.randrange(2):positions=[(positions[0][0],w-mw-positions[0][1]),(positions[1][0],w-tw-positions[1][1])]
    else:
        h=mh+th+rng.randint(5,9);w=max(mw,tw)+rng.randint(5,9)
        gap=rng.randint(2,3);top=rng.randint(1,h-mh-th-gap-1)
        positions=[(top,rng.randrange(w-mw+1)),(top+mh+gap,rng.randrange(w-tw+1))]
        if rng.randrange(2):positions=[(h-mh-positions[0][0],positions[0][1]),(h-th-positions[1][0],positions[1][1])]
    g=[[bg]*w for _ in range(h)]
    for obj,(r0,c0) in zip((mask,tile),positions):
        for r,row in enumerate(obj):
            for c,v in enumerate(row):g[r+r0][c+c0]=v
    parse(g)
    return g


@lru_cache(maxsize=128)
def input_bank(seed):
    integer(seed,0,2**63-1,'seed')
    first=make_input(seed,0,'teach')
    still=[]
    for v in VALUES:
        gold=solve(first,v)
        still.extend((v,r) for r in RIVALS if solve(first,v,r)==gold)
    # Purely demo-driven constructive rejection; no held-out queries consulted.
    for index in range(1,513):
        second=make_input(seed,index,'teach')
        if second!=first and all(solve(second,v,r)!=solve(second,v) for v,r in still):break
    else:raise ValueError('Two-demo teaching construction exhausted')
    demos=[first,second]+[make_input(seed,j,'extra_demo') for j in range(2,6)]
    queries=[make_input(seed,j,'query',stress=j==3) for j in range(4)]
    import json
    if len({json.dumps(g) for g in demos+queries})!=10:raise ValueError('Unexpected duplicate source input')
    # Freeze cached bytes; callers receive freshly decoded ordinary lists.
    return tuple(json.dumps(g,separators=(',',':')) for g in demos),tuple(json.dumps(g,separators=(',',':')) for g in queries)
