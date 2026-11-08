"""Colored-hub docking; source geometry, not stored examples, determines placement."""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import hashlib
import json
import random

VALUES=('matching','opposite')
RIVALS=('other_setting','clockwise_slots','counterclockwise_slots','fixed_color_order',
        'source_position','keep_sources','skip_rotation','only_largest','extra_gap',
        'crop_canvas','fill_hub','mirror_piece')
N8=tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if (r,c)!=(0,0))


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} must be an integer in {low}..{high}; bool is forbidden')
    return value


def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular 1..30 exact-integer color grid')


def components(cells):
    remaining=set(cells);out=[]
    while remaining:
        start=min(remaining);remaining.remove(start);q=[start]
        for r,c in q:
            for dr,dc in N8:
                p=(r+dr,c+dc)
                if p in remaining:remaining.remove(p);q.append(p)
        out.append(sorted(q))
    return out


def bbox(cells):return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)

def rotate(g):return [list(row) for row in zip(*g[::-1])]


def contact(shape,bg,side):
    cells=[(r,c) for r,row in enumerate(shape) for c,v in enumerate(row) if v!=bg]
    h,w=len(shape),len(shape[0])
    if side==0:edge=[c for r,c in cells if r==h-1];span=w
    elif side==1:edge=[r for r,c in cells if c==0];span=h
    elif side==2:edge=[c for r,c in cells if r==0];span=w
    elif side==3:edge=[r for r,c in cells if c==w-1];span=h
    else:raise ValueError('Unknown side')
    edge=sorted(edge)
    return len(edge)==2 and edge[1]==edge[0]+1 and 2*edge[0]+2==span


def orientations(shape,bg,side):
    variants=[];p=[row[:] for row in shape]
    for _ in range(4):
        if contact(p,bg,side) and p not in variants:variants.append(p)
        p=rotate(p)
    return variants


def orient(shape,bg,side):
    possibilities=orientations(shape,bg,side)
    if len(possibilities)!=1:raise ValueError('Missing or ambiguous centered two-cell neck orientation')
    return possibilities[0]


def offset(hr,hc,shape,side,gap=0):
    h,w=len(shape),len(shape[0])
    return [(hr-h-gap,hc+2-w//2),(hr+2-h//2,hc+4+gap),
            (hr+4+gap,hc+2-w//2),(hr+2-h//2,hc-w-gap)][side]


def parse(g):
    grid_check(g);freq=Counter(v for row in g for v in row)
    if sum(x==max(freq.values()) for x in freq.values())!=1:raise ValueError('Expected unique modal background')
    bg=max(freq,key=freq.get)
    groups=components((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg)
    hubs=[cs for cs in groups if len({g[r][c] for r,c in cs})>1]
    if len(hubs)!=1:raise ValueError('Expected exactly one multicolor hub')
    hub=hubs[0];hr,hc,r1,c1=bbox(hub)
    if (r1-hr+1,c1-hc+1)!=(4,4) or len(hub)!=8:raise ValueError('Expected a four-sided 4x4 hub')
    keys=[g[hr][hc+1],g[hr+1][hc+3],g[hr+3][hc+1],g[hr+1][hc]]
    slots=[[(hr,hc+1),(hr,hc+2)],[(hr+1,hc+3),(hr+2,hc+3)],
           [(hr+3,hc+1),(hr+3,hc+2)],[(hr+1,hc),(hr+2,hc)]]
    if len(set(keys))!=4 or bg in keys or set(hub)!={p for ps in slots for p in ps}:
        raise ValueError('Expected four distinct two-cell color keys and an empty center')
    if any(g[r][c]!=key for key,ps in zip(keys,slots) for r,c in ps):raise ValueError('Each slot must have one color')
    parts=[];seen=set()
    for cs in groups:
        if cs is hub:continue
        color=g[cs[0][0]][cs[0][1]]
        if color in seen:raise ValueError('Multiple separate source objects share a color')
        seen.add(color);r0,c0,r2,c2=bbox(cs)
        shape=[row[c0:c2+1] for row in g[r0:r2+1]]
        if any(x not in (bg,color) for row in shape for x in row):raise ValueError('Piece bounding box contains another color')
        parts.append(dict(color=color,cells=cs,box=(r0,c0,r2,c2),shape=shape,size=len(cs)))
    matched=[p for p in parts if p['color'] in keys]
    if not matched:raise ValueError('At least one loose piece must match a hub key')
    for part in matched:
        part['oriented']=[orient(part['shape'],bg,side) for side in range(4)]
        for side in range(4):
            shape=part['oriented'][side];r0,c0=offset(hr,hc,shape,side)
            if r0<0 or c0<0 or r0+len(shape)>len(g) or c0+len(shape[0])>len(g[0]):
                raise ValueError('All supported docking slots must fit within the canvas')
    # All family and directional-rival placements have an unambiguous physical
    # assembly: never let input reading order silently resolve color collisions.
    for shift in range(4):
        occupied=set(hub)
        for part in matched:
            side=(keys.index(part['color'])+shift)%4
            shape=part['oriented'][side];r0,c0=offset(hr,hc,shape,side)
            cells={(r0+r,c0+c) for r,row in enumerate(shape) for c,v in enumerate(row) if v!=bg}
            if occupied & cells:raise ValueError('Docked pieces overlap; ambiguous assembly rejected')
            occupied.update(cells)
    return dict(background=bg,hub=hub,hub_bbox=(hr,hc,r1,c1),keys=keys,parts=parts,matched=matched)


def placements(g,value='matching',rival=None):
    if value not in VALUES:raise ValueError('Unknown docking setting')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    p=parse(g);bg=p['background'];hr,hc,_,_=p['hub_bbox'];keys=p['keys'];selected=p['matched']
    shift=0 if value=='matching' else 2
    if rival=='other_setting':shift=2-shift
    if rival=='clockwise_slots':shift=1
    if rival=='counterclockwise_slots':shift=3
    if rival=='only_largest':selected=[max(selected,key=lambda o:o['size'])]
    result=[]
    for part in selected:
        keyside=keys.index(part['color'])
        if rival=='fixed_color_order':keyside=sorted(keys).index(part['color'])
        if rival=='source_position':
            r0,c0,r1,c1=part['box'];dy=r0+r1-(2*hr+3);dx=c0+c1-(2*hc+3)
            keyside=(1 if dx>=0 else 3) if abs(dx)>=abs(dy) else (2 if dy>=0 else 0)
        side=(keyside+shift)%4
        shape=part['shape'] if rival=='skip_rotation' else part['oriented'][side]
        if rival=='mirror_piece':shape=[row[::-1] for row in shape] if side%2==0 else shape[::-1]
        r0,c0=offset(hr,hc,shape,side,gap=int(rival=='extra_gap'))
        cells=[(r0+r,c0+c) for r,row in enumerate(shape) for c,v in enumerate(row) if v!=bg]
        result.append(dict(color=part['color'],key_side=keyside,destination_side=side,
                           source_bbox=list(part['box']),oriented_shape=shape,translation=[r0,c0],cells=cells))
    return p,result


def solve(g,value='matching',rival=None):
    p,positions=placements(g,value,rival);bg=p['background']
    out=[row[:] for row in g] if rival=='keep_sources' else [[bg]*len(g[0]) for _ in g]
    for r,c in p['hub']:out[r][c]=g[r][c]
    for part in positions:
        for r,c in part['cells']:
            if 0<=r<len(g) and 0<=c<len(g[0]):out[r][c]=part['color']
    if rival=='fill_hub':
        hr,hc,_,_=p['hub_bbox']
        for r in (hr+1,hr+2):
            for c in (hc+1,hc+2):out[r][c]=p['keys'][0]
    if rival=='crop_canvas':
        cells=[(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v!=bg]
        r0,c0,r1,c1=bbox(cells);out=[row[c0:c1+1] for row in out[r0:r1+1]]
    return out


def self_check(g):
    try:parse(g)
    except (ValueError,TypeError,IndexError) as e:return [str(e)]
    return []


def stream(seed,kind,index=0):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**63-1,'index')
    return random.Random(int.from_bytes(hashlib.sha256(f'2c181942:{seed}:{kind}:{index}'.encode()).digest(),'big'))


def source_shape(rng,bg,color,stress=False,asymmetric=False):
    if asymmetric:
        w=8 if stress else 6;h=6 if stress else rng.randint(3,5)
        cells={(0,c) for c in range(w)}|{(r,c) for r in range(1,h) for c in (w//2-1,w//2)}
        cells.add((1,w//2-2))
    else:
        style=rng.choice(('tee','fork','arch','rectangle')) if not stress else rng.choice(('tee','fork'))
        w=8 if stress else rng.choice((4,6));h=rng.randint(5,7) if stress else rng.randint(2,5)
        if style=='rectangle':w=2;h=rng.randint(2,5);cells={(r,c) for r in range(h) for c in range(w)}
        elif style=='arch':h=2;w=4;cells={(0,0),(0,3),(1,1),(1,2)}
        elif style=='fork':
            h=max(h,3);cells={(0,0),(0,w-1)}|{(1,c) for c in range(w)}|{(r,c) for r in range(2,h) for c in (w//2-1,w//2)}
        else:cells={(0,c) for c in range(w)}|{(r,c) for r in range(1,h) for c in (w//2-1,w//2)}
    shape=[[color if (r,c) in cells else bg for c in range(w)] for r in range(h)]
    # Asymmetric internal cells are retained; reflection is not allowed.
    orient(shape,bg,0)
    for _ in range(rng.randrange(4)):shape=rotate(shape)
    return shape


def make_input(seed,index,kind='ordinary',stress=False):
    rng=stream(seed,kind,index);h=w=30 if stress else rng.randint(24,29)
    if not stress:w=rng.randint(24,29)
    colors=rng.sample(range(10),7);bg=colors[0];keys=colors[1:5];extras=colors[5:7]
    hr=h//2-2 if stress else rng.randint(9,h-13);hc=w//2-2 if stress else rng.randint(9,w-13)
    g=[[bg]*w for _ in range(h)]
    slots=[[(hr,hc+1),(hr,hc+2)],[(hr+1,hc+3),(hr+2,hc+3)],
           [(hr+3,hc+1),(hr+3,hc+2)],[(hr+1,hc),(hr+2,hc)]]
    for color,cells in zip(keys,slots):
        for r,c in cells:g[r][c]=color
    use=keys[:] if stress else rng.sample(keys,rng.randint(2,4));rng.shuffle(use)
    shapes=[source_shape(rng,bg,color,stress,asymmetric=i==0) for i,color in enumerate(use)]
    for color in extras[:2 if stress else 1]:
        shapes.append([[color,color],[color,color]])
    rng.shuffle(shapes)
    corners=[0,1,2,3];rng.shuffle(corners)
    # Large source shapes use corners; tiny distractors occupy middle edge slots.
    shapes.sort(key=lambda s:len(s)*len(s[0]),reverse=True)
    for i,shape in enumerate(shapes):
        sh,sw=len(shape),len(shape[0])
        if i<4:
            slot=corners[i];r0=0 if slot<2 else h-sh;c0=0 if slot%2==0 else w-sw
            if not stress:
                r0+=rng.randint(0,2)*(1 if slot<2 else -1)
                c0+=rng.randint(0,2)*(1 if slot%2==0 else -1)
        else:r0=0 if i==4 else h-sh;c0=w//2-sw//2
        for r,row in enumerate(shape):
            for c,v in enumerate(row):g[r+r0][c+c0]=v
    parse(g)
    return g


@lru_cache(maxsize=128)
def input_bank(seed):
    integer(seed,0,2**63-1,'seed');first=make_input(seed,0,'teach');still=[]
    for value in VALUES:
        gold=solve(first,value)
        still.extend((value,rival) for rival in RIVALS if solve(first,value,rival)==gold)
    for i in range(1,513):
        second=make_input(seed,i,'teach')
        if second!=first and all(solve(second,v,r)!=solve(second,v) for v,r in still):break
    else:raise ValueError('Bounded two-demo teaching construction exhausted')
    demos=[first,second]+[make_input(seed,j,'extra_demo') for j in range(2,6)]
    queries=[make_input(seed,j,'query',stress=j==3) for j in range(4)]
    if len({json.dumps(g) for g in demos+queries})!=10:raise ValueError('Unexpected duplicate input')
    return tuple(json.dumps(g,separators=(',',':')) for g in demos),tuple(json.dumps(g,separators=(',',':')) for g in queries)
