"""8f215267: count color-matched external objects into right-aligned frame tallies.

Frame detection and color grouping are geometric; no official grids, output
labels, fixed input positions, or task-specific answer lookup are stored here.
"""
from __future__ import annotations
RULE_TASK_ID = 'ee_8f215267'
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import random

TASK_ID=GENERATOR_ID='public_eval_8f215267'
VERSION='1.0.0'
SUMMARY='Count connected external objects by frame color and encode the counts as spaced dots.'


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high: raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def check_grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected rectangular 1..30 exact-integer color grid')


def components(g,bg,connectivity=4):
    if type(connectivity) is not int or connectivity not in (4,8): raise ValueError('Connectivity must be 4 or 8')
    seen=set(); result=[]
    deltas=[(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr or dc) and (connectivity==8 or abs(dr)+abs(dc)==1)]
    for r,row in enumerate(g):
        for c,color in enumerate(row):
            if color==bg or (r,c) in seen: continue
            todo=[(r,c)];seen.add((r,c));cells=[]
            while todo:
                x,y=todo.pop();cells.append((x,y))
                for dr,dc in deltas:
                    a,b=x+dr,y+dc
                    if 0<=a<len(g) and 0<=b<len(g[0]) and (a,b) not in seen and g[a][b]==color:
                        seen.add((a,b));todo.append((a,b))
            rs=[x for x,y in cells];cs=[y for x,y in cells]
            result.append({'color':color,'cells':sorted(cells),'bbox':(min(rs),min(cs),max(rs),max(cs))})
    return result


def is_frame(obj):
    r1,c1,r2,c2=obj['bbox'];hh=r2-r1+1;ww=c2-c1+1
    return hh>=5 and ww>=7 and len(obj['cells'])==2*(hh+ww)-4 and all(r in (r1,r2) or c in (c1,c2) for r,c in obj['cells'])


def measure(g,connectivity=4):
    check_grid(g);bg=g[0][0]
    frames=[o for o in components(g,bg,4) if is_frame(o)]
    if not frames: raise ValueError('Missing hollow tally frames')
    if len({f['color'] for f in frames})!=len(frames): raise ValueError('Frame colors must be distinct')
    body=deepcopy(g)
    for f in frames:
        for r,c in f['cells']:body[r][c]=bg
    pieces=components(body,bg,connectivity)
    counts=[sum(o['color']==f['color'] for o in pieces) for f in frames]
    for f,n in zip(frames,counts):
        capacity=(f['bbox'][3]-f['bbox'][1]-2)//2
        if n>capacity: raise ValueError('Object count exceeds frame tally capacity')
    return {'background':bg,'frames':frames,'pieces':pieces,'counts':counts}


def solve(g,connectivity=4,*,rival=None):
    if type(connectivity) is not int or connectivity not in (4,8):raise ValueError('Connectivity must be 4 or 8')
    if rival=='opposite_connectivity':connectivity=12-connectivity
    facts=measure(g,connectivity);bg=facts['background'];frames=facts['frames'];pieces=facts['pieces']
    out=deepcopy(g) if rival=='keep_external' else [[bg]*len(g[0]) for _ in g]
    for index,f in enumerate(frames):
        for r,c in f['cells']:out[r][c]=f['color']
        color=(sorted(frames,key=lambda x:x['color'])[index]['color'] if rival=='sorted_color_counts' else f['color'])
        matches=[o for o in pieces if o['color']==color];n=len(matches)
        if rival=='pixel_count_capped':n=sum(len(o['cells']) for o in matches)
        if rival=='distinct_sizes':n=len({len(o['cells']) for o in matches})
        if rival=='ignore_singletons':n=sum(len(o['cells'])>1 for o in matches)
        if rival=='only_rectangular':n=sum(len(o['cells'])==(o['bbox'][2]-o['bbox'][0]+1)*(o['bbox'][3]-o['bbox'][1]+1) for o in matches)
        if rival=='presence_only':n=min(1,n)
        if rival=='global_count':n=len(pieces)
        if rival=='include_frames':n+=1
        r1,c1,r2,c2=f['bbox'];capacity=(c2-c1-2)//2;n=min(capacity,n)
        for k in range(1,n+1):
            col=c1+2*k if rival=='left_aligned' else c2-2*k
            out[(r1+r2)//2][col]=f['color']
    return out


RIVALS=('opposite_connectivity','pixel_count_capped','distinct_sizes','ignore_singletons',
        'only_rectangular','presence_only','global_count','include_frames',
        'sorted_color_counts','left_aligned','keep_external')
SHAPES=(
    ((0,0),),((0,0),(0,1)),((0,0),(1,0)),
    ((0,0),(1,0),(1,1)),((0,0),(0,1),(1,0),(1,1)),
    ((0,1),(1,0),(1,1),(1,2),(2,1)),
    ((0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)),
)
DIAGONALS=(
    ((0,0),(1,1)),
    ((0,0),(0,1),(1,2)),
    ((0,0),(0,1),(1,0),(1,1),(2,2)),
)


def rng_for(seed,slot,attempt=0):
    return random.Random(int.from_bytes(sha256(f'{TASK_ID}:{VERSION}:{seed}:{slot}:{attempt}'.encode()).digest(),'big'))


def transformed(cells,rng):
    pts=list(cells)
    for _ in range(rng.randrange(4)):pts=[(c,-r) for r,c in pts]
    if rng.randrange(2):pts=[(r,-c) for r,c in pts]
    r0=min(r for r,c in pts);c0=min(c for r,c in pts)
    return [(r-r0,c-c0) for r,c in pts]


def scene(seed,slot,attempt=0,stress=False):
    rng=rng_for(seed,slot,attempt)
    h=30 if stress else rng.randint(22,29);w=30 if stress else rng.randint(23,29)
    nframes=4 if stress or (h>=26 and slot>=2 and rng.random()<0.3) else 3
    left=0 if stress else rng.randint(1,2)
    widths=[v for v in (11,13,15) if left+v+2+7<=w]
    fw=15 if stress else rng.choice(widths);fh=5
    bg,*palette=rng.sample(range(10),nframes+3);colors=palette[:nframes];extras=palette[nframes:]
    g=[[bg]*w for _ in range(h)]
    top=1 if stress else rng.randint(1,min(3,h-(6*nframes-1)-1))
    for i,color in enumerate(colors):
        rr=top+6*i
        for r in range(rr,rr+fh):
            for c in range(left,left+fw):
                if r in (rr,rr+fh-1) or c in (left,left+fw-1):g[r][c]=color
    right_start=left+fw+2
    slots=[(r,c) for r in range(1,h-2,4) for c in range(right_start,w-2,4)]
    bottom=top+6*(nframes-1)+fh+2
    slots += [(r,c) for r in range(bottom,h-2,4) for c in range(1,right_start-2,4)]
    if stress:slots=[(r,c) for r,c in slots if r<25];slots.append((27,1))
    rng.shuffle(slots)
    groups=[]
    for i,color in enumerate(colors):
        if stress:
            # Exercise the full six-mark capacity, not only a padded canvas.
            if i==0: shapes=[rng.choice(DIAGONALS) for _ in range(3)]
            elif i==1: shapes=[rng.choice(DIAGONALS) for _ in range(2)]
            elif i==2: shapes=[SHAPES[0],SHAPES[3],SHAPES[-1]]
            else: shapes=[rng.choice(SHAPES) for _ in range(rng.randint(0,2))]
        elif slot==0:
            shapes=[] if i==0 else ([DIAGONALS[0]] if i==1 else [DIAGONALS[0],DIAGONALS[0]])
        elif slot==1:
            shapes=[SHAPES[0]] if i==0 else ([DIAGONALS[0],SHAPES[3]] if i==1 else [SHAPES[3],SHAPES[3]])
        else:
            n=rng.randint(0,2); shapes=[rng.choice(DIAGONALS if rng.random()<0.6 else SHAPES) for _ in range(n)]
        for shape in shapes:groups.append((color,shape))
    # Unlisted colors must disappear without contributing to any frame tally.
    groups.append((extras[0],rng.choice(SHAPES[1:])))
    if not stress:groups.append((extras[1],rng.choice(SHAPES)))
    if len(groups)>len(slots):raise ValueError('Placement capacity')
    for (color,shape),(r,c) in zip(groups,slots):
        for dr,dc in transformed(shape,rng):g[r+dr][c+dc]=color
    if stress:
        for dr,dc in SHAPES[-1]:g[h-3+dr][w-3+dc]=extras[1]
    return g


@lru_cache(maxsize=64)
def bank(seed):
    integer(seed,0,2**63-1,'seed')
    for attempt in range(128):
        try:grids=[scene(seed,slot,attempt,stress=slot==9) for slot in range(10)]
        except ValueError:continue
        if len({str(g) for g in grids})!=10:continue
        lawful=True
        try:
            for g in grids:
                measure(g,4);measure(g,8)
            for con in (4,8):
                labels=[solve(g,con) for g in grids[:2]]
                for rival in RIVALS:
                    if all(solve(g,con,rival=rival)==y for g,y in zip(grids[:2],labels)) and any(solve(g,con,rival=rival)!=solve(g,con) for g in grids[6:]):
                        lawful=False;break
                if not lawful:break
        except ValueError:lawful=False
        if lawful:return tuple(grids)
    raise ValueError('Bounded constructive lesson sampler exhausted 128 attempts')


def generate(seed,sample_index,*,difficulty=None,**overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    if overrides:raise ValueError('Unknown controls: '+','.join(sorted(overrides)))
    return deepcopy(scene(seed,sample_index,stress=difficulty=='hard' or sample_index%10==9))


def self_check(grid,*,difficulty=None,meta=None):
    try:measure(grid,4)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
