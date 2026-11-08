"""Framed topological selector, deterministic grammar, and independent Python oracle."""
from __future__ import annotations
import copy
import hashlib
import random


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid_check(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list or not 1 <= len(g[0]) <= 30
            or any(type(row) is not list or len(row) != len(g[0]) or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular exact-color grid of size 1..30')
    return g


def components(cells, connectivity=4):
    unseen = set(cells); result = []
    offsets = ((-1,0),(0,-1),(0,1),(1,0)) if connectivity == 4 else tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c)
    while unseen:
        root = min(unseen); unseen.remove(root); stack = [root]; part = {root}
        while stack:
            r,c = stack.pop()
            for dr,dc in offsets:
                p = (r+dr,c+dc)
                if p in unseen:
                    unseen.remove(p); part.add(p); stack.append(p)
        result.append(part)
    return result


def analyze(g):
    grid_check(g); h,w=len(g),len(g[0]); frame=g[0][0]
    active_rows=[r for r in range(h) if any(v!=frame for v in g[r])]
    if not active_rows or active_rows != list(range(min(active_rows),max(active_rows)+1)):
        raise ValueError('Need one contiguous framed row band')
    top,bottom=active_rows[0],active_rows[-1]
    separators={c for c in range(w) if all(g[r][c]==frame for r in range(h))}
    runs=[]
    for c in range(w):
        if c not in separators and (c==0 or c-1 in separators):
            end=c
            while end+1<w and end+1 not in separators:end+=1
            runs.append((c,end))
    if len(runs)!=4 or len({b-a+1 for a,b in runs})!=1 or 0 not in separators or w-1 not in separators:
        raise ValueError('Need four equal framed panels')
    panels=[[row[a:b+1]for row in g[top:bottom+1]]for a,b in runs]
    ph,pw=len(panels[0]),len(panels[0][0]);bg=panels[3][0][0]
    if bg==frame or any(v!=bg for row in panels[3]for v in row):raise ValueError('Fourth panel must be blank')
    colors={v for row in panels[0]for v in row if v!=bg}
    if len(colors)!=1:raise ValueError('Selector needs one ink color')
    selector={(r,c)for r in range(ph)for c in range(pw)if panels[0][r][c]!=bg}
    pieces=sorted(components(selector,8),key=lambda x:(len(x),min(x)))
    if len(pieces)!=2 or len(pieces[0])!=1 or len(pieces[1])<3:
        raise ValueError('Need a singleton marker separate from an 8-connected divider')
    marker=next(iter(pieces[0]));barrier=pieces[1]
    universe={(r,c)for r in range(ph)for c in range(pw)}
    regions=components(universe-barrier)
    if len(regions)!=2:raise ValueError('Divider must cut the panel into exactly two 4-connected regions')
    region=next(x for x in regions if marker in x)
    return dict(top=top,bottom=bottom,runs=runs,ph=ph,pw=pw,bg=bg,frame=frame,
                selector=panels[0],sources=panels[1:3],marker=marker,barrier=barrier,region=region,
                other=universe-barrier-region,universe=universe)


def render(g, info, region, marker_first=True, boundary=True, first_priority=True):
    out=copy.deepcopy(g);a,b=info['sources'];bg=info['bg'];barrier=info['barrier']
    selected=set(region) if marker_first else info['universe']-barrier-set(region)
    for r in range(info['ph']):
        for c in range(info['pw']):
            p=(r,c);on=p in barrier
            eligible_a=(p in selected) or (on and boundary)
            eligible_b=(not on and p not in selected) or (on and boundary)
            x=a[r][c] if eligible_a else bg;y=b[r][c]if eligible_b else bg
            value=x if (x!=bg and (first_priority or y==bg)) else y
            out[info['top']+r][info['runs'][3][0]+c]=value
    return out


def solve(g,assignment='marker_first'):
    if assignment not in ('marker_first','marker_second'):raise ValueError('Unknown assignment')
    info=analyze(g)
    return render(g,info,info['region'],assignment=='marker_first')


def rng_for(seed,tag):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:selector:{tag}'.encode()).digest(),'big'))


def sample_grid(seed,tag,profile):
    """profile: panel height, width, divider kind, chosen side, extra right frame."""
    ph,pw,kind,side,pad=profile;rng=rng_for(seed,tag)
    frame,bg,ink,ca,cb=rng.sample(range(10),5)
    if kind=='diagonal':
        barrier={(r,r)for r in range(ph)}
        if rng.randrange(2):barrier={(r,pw-1-c)for r,c in barrier}
    elif kind=='elbow':
        cut_r=ph//2;cut_c=pw//2
        barrier={(r,cut_c)for r in range(cut_r+1)}|{(cut_r,c)for c in range(cut_c,pw)}
    elif kind=='horizontal':
        cut=ph//2+(rng.randrange(3)-1)
        barrier={(cut,c)for c in range(pw)}
    elif kind=='stair':
        barrier={(r,2+(r//4)%2)for r in range(ph)}
    else:
        barrier={(r,pw//2)for r in range(ph)}
    universe={(r,c)for r in range(ph)for c in range(pw)}
    regions=components(universe-barrier)
    if len(regions)!=2:raise ValueError('Invalid constructive profile')
    candidates=[p for p in sorted(regions[side]) if all(max(abs(p[0]-r),abs(p[1]-c))>1 for r,c in barrier)]
    if not candidates:raise ValueError('Profile leaves no isolated marker')
    marker=rng.choice(candidates)
    selector=[[ink if (r,c)in barrier or (r,c)==marker else bg for c in range(pw)]for r in range(ph)]
    a=[[ca if rng.random()<0.55 else bg for _ in range(pw)]for _ in range(ph)]
    b=[[cb if rng.random()<0.55 else bg for _ in range(pw)]for _ in range(ph)]
    # Mandatory diagnostics in both regions make assignment, copying and union
    # rivals observable, independent of palette and randomized filler.
    for region in regions:
        for r,c in rng.sample(sorted(region),min(3,len(region))):a[r][c]=ca;b[r][c]=cb
    line=sorted(barrier);r,c=line[len(line)//2];a[r][c]=ca;b[r][c]=cb
    r,c=line[0];a[r][c]=bg;b[r][c]=cb
    panels=[selector,a,b,[[bg]*pw for _ in range(ph)]]
    width=4*pw+5+pad
    g=[[frame]*width]
    for r in range(ph):g.append([frame]+sum([p[r]+[frame]for p in panels],[])+[frame]*pad)
    g.append([frame]*width)
    analyze(g)
    return g


def bank(seed):
    demo_profiles=[(5,5,'diagonal',seed%2,0),(28,6,'elbow',1,0),(7,5,'horizontal',0,0),
                   (11,6,'stair',1,0),(14,5,'vertical',0,0),(19,6,'elbow',0,0)]
    query_profiles=[(6,6,'diagonal',1,0),(12,6,'elbow',0,0),(20,5,'horizontal',1,0),(28,6,'stair',seed%2,1)]
    train=[sample_grid(seed,f'demo:{i}',p)for i,p in enumerate(demo_profiles)]
    queries=[sample_grid(seed,f'query:{i}',p)for i,p in enumerate(query_profiles)]
    rng_for(seed,'presentation').shuffle(queries)
    return train,queries
