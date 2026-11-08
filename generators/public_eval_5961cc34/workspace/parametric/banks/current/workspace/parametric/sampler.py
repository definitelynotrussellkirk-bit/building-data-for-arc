"""Constructive relay networks with inert distractors, cycles, and D4 variation."""
import hashlib
import random

PATHS = (
    ((2,0),(2,1),(1,1),(1,2),(0,2)),
    ((2,1),(1,1),(1,0),(0,0),(0,1),(0,2)),
    ((2,2),(2,1),(1,1),(1,2),(0,2),(0,1),(0,0)),
    ((2,0),(2,1),(1,1),(1,0)), # closed loop
    ((2,1),(1,1),(1,2)),
    ((2,2),(1,2),(1,1),(2,1),(2,0),(1,0),(0,0)),
)


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an integer in {lo}..{hi}')
    return value


def transform(g,index):
    integer(index,0,7,'transform')
    out=[row[:] for row in g]
    if index>=4:out=[row[::-1] for row in out]
    for _ in range(index%4):out=[list(row) for row in zip(*out[::-1])]
    return out


def draw(seed,index,*,split='train',grid_h=None,grid_w=None,transform_id=None,path_id=None,band=None):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'sample_index')
    if split not in ('train','test','production'):raise ValueError('Unknown stream')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'beam-v1:{seed}:{split}:{index}'.encode()).digest(),'big'))
    stress=split=='test' and index==3
    h=30 if stress else rng.randint(24,29)
    w=30 if stress else rng.randint(24,29)
    if grid_h is not None:h=integer(grid_h,24,30,'grid_h')
    if grid_w is not None:w=integer(grid_w,24,30,'grid_w')
    b=rng.choice((1,2)) if band is None else integer(band,1,2,'band')
    orient_rng=random.Random(f'beam-orientation-v1:{seed}:{split}:{index}')
    t=orient_rng.choice((0,2)) if split=='train' and index==0 else orient_rng.randrange(8)
    if transform_id is not None:t=integer(transform_id,0,7,'transform_id')
    # Controls describe the returned grid, not the pre-rotation workspace.
    if t%2:h,w=w,h
    cap=3 if min(h,w)==30 else 2
    ys=[cap,(cap+h-b-cap-3)//2,h-b-cap-3]
    xs=[cap,(cap+w-b-cap)//2,w-b-cap]
    k=(1 if split=='train' and index==0 else rng.randrange(len(PATHS))) if path_id is None else integer(path_id,0,5,'path_id')
    path=PATHS[k]
    g=[[8]*w for _ in range(h)]
    occupied=set()
    # Include at least one unreachable, deliberately large decoy. At stress
    # size all nine nodes occupy the full canvas rather than merely padding it.
    rest=sorted(set((r,c) for r in range(3) for c in range(3))-set(path))
    rng.shuffle(rest);decoys=rest if stress else rest[:rng.randint(1,len(rest))]
    for slot in list(path)+decoys:
        i=path.index(slot) if slot in path else None
        radius=cap if i==0 or i is None else rng.randint(1,max(1,cap-1))
        ry=radius;rx=radius
        y,x=ys[slot[0]],xs[slot[1]]
        r0,r1=y-ry,y+b+ry-1;c0,c1=x-rx,x+b+rx-1
        # Corner clipping changes occupied area without changing aligned ports.
        clipped=rng.choice((False,True))
        cells={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)
               if not(clipped and r in (r0,r1) and c in (c0,c1))}
        if occupied & cells:raise AssertionError('Construction overlapped relay cells')
        occupied|=cells
        for r,c in cells:g[r][c]=1
        if i is None:dr,dc=rng.choice(((-1,0),(0,1),(1,0),(0,-1)))
        elif i+1<len(path):dr,dc=path[i+1][0]-slot[0],path[i+1][1]-slot[1]
        elif k==3:dr,dc=1,0
        elif slot[0]==0:dr,dc=-1,0
        else:dr,dc=0,1
        markers=([(r0 if dr<0 else r1,c) for c in range(x,x+b)] if dr else
                 [(r,c0 if dc<0 else c1) for r in range(y,y+b)])
        for r,c in markers:g[r][c]=3
    gun_c=xs[path[0][1]]+rng.randrange(b)
    g[h-2][gun_c]=4;g[h-1][gun_c]=2
    # The first lesson deliberately separates reading order from causal depth.
    return transform(g,t)
