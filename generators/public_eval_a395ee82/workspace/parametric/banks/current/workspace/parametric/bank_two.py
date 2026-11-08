"""Sparse diagram -> normalized offsets -> dimension-scaled motif stamping.

No official grids, solutions, or sibling source are used by this sampler.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
import random

SETTINGS = ('as_drawn', 'clockwise')

def _grid(g):
    if type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list or not 1 <= len(g[0]) <= 30:
        raise ValueError('Expected a nonempty ARC grid')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('Expected rectangular exact integer colors')
    return g

def _components(g, bg):
    seen=set(); out=[]
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if v==bg or (r,c) in seen: continue
            stack=[(r,c)];seen.add((r,c));cells=[]
            while stack:
                p=stack.pop();cells.append(p)
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    q=(p[0]+dr,p[1]+dc)
                    if 0<=q[0]<len(g) and 0<=q[1]<len(row) and q not in seen and g[q[0]][q[1]]==v:
                        seen.add(q);stack.append(q)
            out.append((v,cells))
    return out

def parse(g):
    _grid(g)
    counts={v:sum(row.count(v) for row in g) for v in range(10)}
    bg=max(counts,key=counts.get)
    objects=_components(g,bg)
    big=[o for o in objects if len(o[1])>1]
    if len(big)!=1: raise ValueError('Expected one connected nonsingleton motif')
    color,cells=big[0]
    anchors=[o[1][0] for o in objects if len(o[1])==1 and o[0]==color]
    if len(anchors)!=1:raise ValueError('Expected one same-color singleton anchor')
    marker_colors={v for v,cs in objects if v!=color}
    if len(marker_colors)!=1:raise ValueError('Expected one diagram marker color')
    other=next(iter(marker_colors))
    markers=[p for v,cs in objects if v==other for p in cs]
    if any(len(cs)!=1 for v,cs in objects if v==other): raise ValueError('Diagram markers must be isolated')
    ar,ac=anchors[0];drs=[r-ar for r,c in markers];dcs=[c-ac for r,c in markers]
    sy=math.gcd(*drs) or 1;sx=math.gcd(*dcs) or 1
    r0=min(r for r,c in cells);c0=min(c for r,c in cells)
    h=max(r for r,c in cells)-r0+1;w=max(c for r,c in cells)-c0+1
    offsets=[(dy//sy,dx//sx) for dy,dx in zip(drs,dcs)]
    return dict(bg=bg,color=color,other=other,cells=cells,origin=(r0,c0),h=h,w=w,offsets=offsets,pitch=(sy,sx))

def solve(g, layout='as_drawn', *, rival=None):
    if layout not in SETTINGS: raise ValueError('Unknown layout')
    d=parse(g);h,w=len(g),len(g[0]);out=[[d['bg']]*w for _ in range(h)]
    mh,mw=d['h'],d['w']
    if rival=='unit_scale':mh=mw=1
    if rival=='square_scale':mw=mh
    offsets=d['offsets']
    if layout=='clockwise': offsets=[(c,-r) for r,c in offsets]
    if rival=='unrotated':offsets=d['offsets']
    if rival=='counterclockwise':offsets=[(-c,r) for r,c in d['offsets']]
    if rival=='transpose':offsets=[(c,r) for r,c in d['offsets']]
    if rival=='reverse':offsets=[(-r,-c) for r,c in d['offsets']]
    if rival=='first_only':offsets=offsets[:1]
    center_color=d['color'] if rival=='keep_center_color' else d['other']
    if rival=='retain_diagram':out=copy.deepcopy(g)
    def stamp(dy,dx,color):
        for r,c in d['cells']:
            rr,cc=r+dy*mh,c+dx*mw
            if 0<=rr<h and 0<=cc<w:out[rr][cc]=color
    stamp(0,0,center_color)
    for dy,dx in offsets:stamp(dy,dx,d['color'])
    return out



def _rng(seed,split,index):
    return random.Random(int.from_bytes(hashlib.sha256(f'a395-v1:{seed}:{split}:{index}'.encode()).digest(),'big'))

def sample(seed,split,index):
    rng=_rng(seed,split,index)
    # Query ordinal is a private coverage schedule, never public presentation order.
    if split=='test':
        size=((20,22),(24,25),(27,29),(30,30))[index]
        mh,mw=((3,4),(4,3),(5,4),(6,6))[index]
    else:
        size=((22,24),(24,22),(25,26),(26,28),(28,26),(29,29))[index]
        mh,mw=((3,4),(4,3),(4,4),(4,5),(5,4),(5,5))[index]
    h,w=size; bg,color,other=rng.sample(range(10),3)
    g=[[bg]*w for _ in range(h)]
    # One connected asymmetric motif; full edge backbone keeps random holes safe.
    cells={(r,c) for r in range(mh) for c in range(mw)}
    cells.remove((0,0))
    for r in range(1,mh-1):
        for c in range(1,mw-1):
            if rng.random()<.35: cells.discard((r,c))
    # Hole carving may isolate an interior island. Retain only the component
    # reached from the perimeter, never a second source-colored singleton.
    seen={(0,1)};stack=[(0,1)]
    while stack:
        r,c=stack.pop()
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(r+dr,c+dc)
            if q in cells and q not in seen:seen.add(q);stack.append(q)
    cells=seen
    r0,c0=2*mh,2*mw
    for r,c in cells:g[r0+r][c0+c]=color
    offsets={(-2,0),(0,2),(2,-1),(-1,-2),(1,0)}
    choices=[(-2,1),(-1,1),(1,2),(2,1),(0,-2)]
    offsets.update(rng.sample(choices,1+index%3))
    # Flip the diagram independently of the rule setting; retain a primitive lattice.
    sr,sc=rng.choice((-1,1)),rng.choice((-1,1))
    offsets={(sr*r,sc*c) for r,c in offsets}
    # Two or three pixel pitch where it fits; diagram always separate from the motif.
    pitch=rng.choice((2,3))
    ar,ac=h-1-2*pitch,w-1-2*pitch
    g[ar][ac]=color
    for dr,dc in offsets:g[ar+pitch*dr][ac+pitch*dc]=other
    return g



# Ordinary generator entry point is self-contained under runtime relocation.
GENERATOR_ID=TASK_ID='public_eval_a395ee82'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
AXES={}
SUMMARY='Decode a sparse map and scale motif stamps'
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
