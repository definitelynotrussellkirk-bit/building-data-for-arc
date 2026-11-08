"""Constructive nonbranching gate mazes; no retries, clipping, or count fallback."""
import hashlib
import random


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an integer in {lo}..{hi}')
    return value


def draw(seed,index,*,split='train',grid_h=None,grid_w=None,holes=None,gates_per_lane=None,reflection=None,phase=None):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'sample_index')
    if split not in ('train','test','production'):raise ValueError('Unknown input stream')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'gate-paths-v1:{seed}:{split}:{index}'.encode()).digest(),'big'))
    if split=='test':
        h=[18+seed%2,22+seed%2,28,30][index%4];w=[25,26,29,30][index%4]
    else:
        h=9+3*(index%6)+seed%3;w=16+(seed+index)%9
    if grid_h is not None:h=integer(grid_h,9,30,'grid_h')
    if grid_w is not None:w=integer(grid_w,16,30,'grid_w')
    phase=rng.randrange(2) if phase is None else integer(phase,0,1,'phase')
    bands=list(range(phase,h,2));lanes=[r+1 for r in bands[:-1]]
    # Adjacent lanes use disjoint alternating column pools. Every common cyan
    # row then has at most one vertical edge at a vertex and degree <= 2.
    offset=rng.randint(4,6)
    if gates_per_lane is not None:
        integer(gates_per_lane,1,3,'gates_per_lane');offset=4
    centers=list(range(offset,w-2,4));pools=(centers[::2],centers[1::2])
    if not all(pools):raise ValueError('Canvas cannot fit both gate-column phases')
    if gates_per_lane is not None and any(len(p)<gates_per_lane for p in pools):
        raise ValueError('Exact gate count cannot fit the requested width with safe adjacent lanes')
    g=[[0]*w for _ in range(h)]
    for r in bands:
        g[r]=[8]*w
        if r!=bands[-1]:g[r][0]=g[r][-1]=3
    gates=[]
    include_empty=(split=='train' and index%3==1) or (split=='test' and index%4 in (1,3)) or (split=='production' and index%4==1)
    empty_lane=len(lanes)//2 if include_empty and gates_per_lane is None else -1
    for i,r in enumerate(lanes):
        if i==empty_lane:continue
        pool=pools[i%2]
        minimum=2 if split=='test' and index==3 and len(pool)>=2 else 1
        n=gates_per_lane if gates_per_lane is not None else rng.randint(minimum,min(3,len(pool)))
        for c in sorted(rng.sample(pool,n)):
            g[r][c-1:c+2]=[7,7,7];gates.append((r,c))
    count=(2 if index%3==0 or split=='test' else 0 if index%3==1 else 1) if holes is None else integer(holes,0,4,'holes')
    # The first and last cyan rows contain a genuine interior dead end. It is
    # not enough to remember the original left/right margin of the marker.
    chosen=[(bands[0],2),(bands[-1],2)][:count]
    blocked={(r+dr,c+dc) for r,c in gates for dr,dc in [(-1,-1),(-1,0),(-1,1),(1,-1),(1,0),(1,1)]}
    candidates=[(r,c) for r in bands for c in range(2,w-2)
                if (r,c) not in blocked and (r,c) not in chosen]
    rng.shuffle(candidates)
    if len(candidates)<count-len(chosen):raise ValueError('Requested holes are infeasible')
    chosen+=candidates[:count-len(chosen)]
    for r,c in chosen:g[r][c]=0
    reflect=rng.randrange(4) if reflection is None else integer(reflection,0,3,'reflection')
    if reflect&1:g=[row[::-1] for row in g]
    if reflect&2:g=g[::-1]
    return g
