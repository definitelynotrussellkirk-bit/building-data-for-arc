"""Measure enclosed 4-connected regions, then apply the scene's color legend."""
from __future__ import annotations
RULE_TASK_ID = 'ee_e3721c99'
import copy
from functools import lru_cache
import hashlib
import random
from pathlib import Path
SETTINGS=('exact','nearest_lower')
D4=((1,0),(-1,0),(0,1),(0,-1))

def _grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('Expected a nonempty ARC grid')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('Expected rectangular exact integer colors')
    return g

def components(g):
    seen=set();out=[]
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if not v or (r,c) in seen:continue
            todo=[(r,c)];seen.add((r,c));cells=[]
            while todo:
                p=todo.pop();cells.append(p)
                for dr,dc in D4:
                    q=(p[0]+dr,p[1]+dc)
                    if 0<=q[0]<len(g) and 0<=q[1]<len(row) and q not in seen and g[q[0]][q[1]]==v:
                        todo.append(q);seen.add(q)
            out.append((v,cells))
    return out

def holes(cells,*,diagonal=False,include_exterior=False):
    cells=set(cells)
    if not cells:raise ValueError('Cannot measure an empty object')
    r0=min(r for r,c in cells);r1=max(r for r,c in cells);c0=min(c for r,c in cells);c1=max(c for r,c in cells)
    unseen={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}-cells
    deltas=D4+(((1,1),(1,-1),(-1,1),(-1,-1)) if diagonal else ())
    out=[]
    while unseen:
        start=min(unseen);unseen.remove(start);todo=[start];region=[]
        while todo:
            p=todo.pop();region.append(p)
            for dr,dc in deltas:
                q=(p[0]+dr,p[1]+dc)
                if q in unseen:unseen.remove(q);todo.append(q)
        if include_exterior or not any(r in (r0,r1) or c in (c0,c1) for r,c in region):out.append(region)
    return out

def parse(g):
    _grid(g);os=components(g);h,w=len(g),len(g[0]);legend={};prototypes=[];payload=[]
    for color,cells in os:
        if color==5:payload.append(cells);continue
        if any(r in (0,h-1) or c in (0,w-1) for r,c in cells):continue
        n=len(holes(cells))
        if n in legend and legend[n]!=color:raise ValueError('Ambiguous legend hole counts')
        legend[n]=color;prototypes.append((n,color,cells))
    if not legend or not payload:raise ValueError('Expected a non-gray legend and gray objects')
    return legend,payload,prototypes

def solve(g,lookup='exact',*,rival=None):
    if lookup not in SETTINGS:raise ValueError('Unknown lookup rule')
    legend,payload,prototypes=parse(g);out=copy.deepcopy(g)
    if rival=='color_order':legend=dict(zip(sorted(legend),sorted(legend.values())))
    if rival=='reverse_color_order':legend=dict(zip(sorted(legend),sorted(legend.values(),reverse=True)))
    if rival=='legend_position_rank':legend={i:p[1] for i,p in enumerate(prototypes)}
    for cells in payload:
        regions=holes(cells,diagonal=rival=='eight_connected',include_exterior=rival=='bbox_zero_regions')
        n=sum(map(len,regions)) if rival=='hole_area' else len(regions)
        if rival=='cap_at_one':n=min(1,n)
        if rival=='nearest_upper':
            keys=[k for k in legend if k>=n];color=legend[min(keys)] if keys else 0
        elif lookup=='nearest_lower':
            keys=[k for k in legend if k<=n];color=legend[max(keys)] if keys else 0
        else:color=legend.get(n,0)
        if rival=='keep_unmatched' and n not in legend:color=5
        for r,c in cells:out[r][c]=color
    return out



def _connected(cells):
    if not cells:return False
    seen={min(cells)};todo=list(seen)
    while todo:
        r,c=todo.pop()
        for dr,dc in D4:
            q=(r+dr,c+dc)
            if q in cells and q not in seen:seen.add(q);todo.append(q)
    return len(seen)==len(cells)

def _shape(rng,height,width,count):
    cells={(r,c) for r in range(height) for c in range(width)}
    centers=[(r,c) for r in range(1,height-1,2) for c in range(1,width-1,2)]
    # A diagonal opening must not collapse a four-connected cavity.
    chosen=([(1,1)]+rng.sample([p for p in centers if p!=(1,1)],count-1)) if count else []
    cells.difference_update(chosen);cells.discard((0,0))
    # Enlarge holes without merging them. Single-hole objects always teach area != count.
    candidates=[(r+dr,c+dc) for r,c in chosen for dr,dc in D4];rng.shuffle(candidates)
    for q in candidates:
        if q in cells and 0<q[0]<height-1 and 0<q[1]<width-1:
            trial=cells-{q}
            if _connected(trial) and len(holes(trial))==count:
                cells=trial
                if count==1 or rng.random()<.5:break
    # Nonrectangular contours and open exterior pockets are not enclosed holes.
    boundary=[p for p in sorted(cells) if p[0] in (0,height-1) or p[1] in (0,width-1)]
    rng.shuffle(boundary)
    for q in boundary[:max(2,len(boundary)//3)]:
        trial=cells-{q}
        if (trial and min(r for r,c in trial)==0 and max(r for r,c in trial)==height-1
                and min(c for r,c in trial)==0 and max(c for r,c in trial)==width-1
                and _connected(trial) and len(holes(trial))==count):cells=trial
    assert _connected(cells) and len(holes(cells))==count
    return cells

@lru_cache(maxsize=512)
def _sample(seed,split,index):
    rng=random.Random(int.from_bytes(hashlib.sha256(f'e372-v1:{seed}:{split}:{index}'.encode()).digest(),'big'))
    sizes=((20,22),(24,25),(27,29),(30,30)) if split=='test' else ((22,24),(24,22),(25,26),(26,28),(28,26),(29,29))
    h,w=sizes[index]
    keys=([0,2],[1,3],[0,2,4],[1,2,4],[0,3],[1,3,4])[index]
    colors=rng.sample([1,2,3,4,6,7,8,9],len(keys))
    # Teach both palette orders, then use unconstrained query assignments.
    if split=='train' and index<2:colors.sort(reverse=index==0)
    legend=list(zip(keys,colors));rng.shuffle(legend)
    g=[[0]*w for _ in range(h)]
    widths=[3 if n==0 else 2*n+1 for n,c in legend]
    total=sum(widths)+len(widths)-1
    offset=rng.randint(1,w-total-1)
    for (n,color),width in zip(legend,widths):
        for r in range(3):
            for c in range(width):
                if n==0 or r!=1 or c%2==0:g[r+1][c+offset]=color
        offset+=width+1
    divider=rng.choice([1,2,3,4,6,7,8,9]);g[5]=[divider]*w
    slot_h=(h-8)//2;slot_w=(w-2)//3
    counts=[0,1,2,3,1,0] if index<2 else [0,1,2,3,4,5]
    rng.shuffle(counts)
    for k,n in enumerate(counts):
        low=7 if n>=5 else 5
        sh=rng.randint(low,slot_h);sw=rng.randint(low,slot_w)
        rr=7+(k//3)*(slot_h+1)+rng.randint(0,slot_h-sh)
        cc=(k%3)*(slot_w+1)+rng.randint(0,slot_w-sw)
        cells=_shape(rng,sh,sw,n)
        for r,c in cells:g[rr+r][cc+c]=5
    # Whole-scene rotations/reflections preserve topology and change legend side.
    for _ in range(rng.randrange(4)):g=[list(row) for row in zip(*g[::-1])]
    if rng.randrange(2):g=[row[::-1] for row in g]
    return tuple(tuple(row) for row in g)

def sample(seed,split,index):return [list(row) for row in _sample(seed,split,index)]



# Ordinary generator entry point is self-contained under runtime relocation.
GENERATOR_ID=TASK_ID='public_eval_e3721c99'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
AXES={}
SUMMARY='Count enclosed four-connected cavities and apply the scene legend'
INVARIANTS=['Deterministic scene sampler; canonical labels belong to reference.rkt','No official-data, sibling-module or sidecar imports']
def generate(seed,sample_index,*,difficulty=None,**overrides):
    if overrides:raise ValueError('No advertised override axes')
    if type(seed) is not int or seed<0 or type(sample_index) is not int or sample_index<0:raise ValueError('Exact nonnegative seed/index required')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unsupported difficulty')
    return sample(seed+1000003*(sample_index//6),'train',sample_index%6)
def self_check(grid):
    try:parse(grid)
    except (TypeError,ValueError,IndexError) as e:return [str(e)]
    return []
