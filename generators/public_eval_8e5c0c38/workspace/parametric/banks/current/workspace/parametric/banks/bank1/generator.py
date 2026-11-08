"""Standalone input sampler for per-color maximum-support vertical symmetry.

No adjacent resources are needed by the ordinary generate() API. The native
adapter carries a byte-identical copy inside its permitted resource boundary.
Python predictions are audit/adapter claims; protected Racket is label authority.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import random

GENERATOR_ID = 'public_eval_8e5c0c38'
TASK_ID = GENERATOR_ID
RULE_TASK_ID = 'ee_8e5c0c38'
VERSION = '1.0.0'
SUMMARY = 'Infer each color\'s vertical symmetry axis and remove unmatched pixels.'
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
        any(type(row) is not list for row in grid) or not 1 <= len(grid[0]) <= 30 or
        any(len(row) != len(grid[0]) for row in grid) or
        any(type(x) is not int or not 0 <= x <= 9 for row in grid for x in row)):
        raise ValueError('expected rectangular 1..30 integer-color grid')
    return grid

def records(grid, policy='support'):
    validate_grid(grid)
    counts = Counter(x for row in grid for x in row)
    bg = min(counts, key=lambda x: (-counts[x], x))
    out=[]
    for color in sorted(set(counts)-{bg}):
        cells={(r,c) for r,row in enumerate(grid) for c,x in enumerate(row) if x==color}
        axis_dim = 0 if policy=='horizontal' else 1
        best = max(range(2*len(grid if axis_dim==0 else grid[0])-1),
                   key=lambda k: (sum(((k-r,c) if axis_dim==0 else (r,k-c)) in cells for r,c in cells),
                                  k if policy=='rightmost' else -k))
        if policy=='bbox': best=min(p[1] for p in cells)+max(p[1] for p in cells)
        if policy=='canvas': best=len(grid[0])-1
        out.append(dict(color=color,cells=sorted(cells),axis_twice=best,dimension=axis_dim))
    return bg,out

def predict(grid, mode='trim', policy='support'):
    if mode not in ('trim','complete'): raise ValueError('unknown repair mode')
    bg,parts=records(grid,policy)
    out=[[bg]*len(grid[0]) for _ in grid]
    for part in parts:
        pts=set(map(tuple,part['cells'])); k=part['axis_twice']; dim=part['dimension']
        mirror={(k-r,c) if dim==0 else (r,k-c) for r,c in pts}
        keep=pts&mirror if mode=='trim' else pts|mirror
        for r,c in keep:
            if 0<=r<len(grid) and 0<=c<len(grid[0]):out[r][c]=part['color']
    return out

def _mask(rng, hh, ww, kind):
    """Symmetric connected support plus one-sided, bbox-extending corruptions."""
    if kind=='tie':
        return {(0,0),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3),(2,1)}
    # A solid interior spine with randomized symmetric row extents keeps the
    # support connected, while row variability defeats horizontal symmetry.
    axis=ww-1
    core=set()
    for r in range(hh):
        margin=rng.randrange(max(1,(ww-2)//2))
        for c in range(1+margin,ww-1-margin):
            # Paired holes expose a filled-bounding-box shortcut.
            if 0<r<hh-1 and abs(2*c-axis)>2 and rng.random()<0.18:
                continue
            core.add((r,c));core.add((r,axis-c))
    # Enforce a nonempty horizontal bridge, and distinct per-row extents.
    for c in range(1,ww-1):core.add((hh//2,c))
    cells=set(core)
    side=rng.choice([0,ww-1])
    for r in rng.sample(range(hh), max(1,hh//3)):
        cells.add((r,side))
    # Keep only constructions where the intended axis actually maximizes score.
    candidates=range(2*ww-1)
    selected=max(candidates,key=lambda k:(sum((r,k-c) in cells for r,c in cells),-k))
    if selected!=axis or cells=={(r,axis-c) for r,c in cells}:
        return None
    return cells

def sample(seed, index):
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('seed must be nonnegative exact integer below 2**63')
    if type(index) is not int or index<0:raise ValueError('index must be nonnegative exact integer')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'{TASK_ID}:{seed}:{index}'.encode()).digest(),'big'))
    profiles=[(14,17),(19,21),(25,27),(30,30)]
    if 100<=index<=103:h,w=profiles[index-100]
    else:
        h,w=rng.choice([(14,17),(18,20),(22,24),(25,27)])
    bg=rng.randrange(10);palette=rng.sample([x for x in range(10) if x!=bg],4)
    grid=[[bg]*w for _ in range(h)]
    bh,bw=h//2,w//2
    n=4 if (index==103 or index%3==1) else 3
    tiles=[(0,0,bh,bw),(0,bw,bh,w-bw),(bh,0,h-bh,bw),(bh,bw,h-bh,w-bw)]
    rng.shuffle(tiles)
    for j,(r0,c0,th,tw) in enumerate(tiles[:n]):
        tie=(index%3==0 and j==0)
        hh=3 if tie else rng.randint(max(3,th-5),th-2)
        ww=4 if tie else rng.randint(max(5,tw-5),tw-2)
        for _ in range(128):
            pts=_mask(rng,hh,ww,'tie' if tie else 'random')
            if pts is not None:break
        else:raise RuntimeError('bounded symmetric-mask construction failed')
        # Edge contact on the max case; interior offsets vary elsewhere.
        rr=r0+(0 if r0==0 and index==103 else th-hh if index==103 else rng.randrange(th-hh+1))
        cc=c0+(0 if c0==0 and index==103 else tw-ww if index==103 else rng.randrange(tw-ww+1))
        for r,c in pts:grid[rr+r][cc+c]=palette[j]
    return grid

def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if overrides:raise ValueError('this sampler exposes no override axes')
    return sample(seed,sample_index)

def self_check(grid, **_):
    try:
        validate_grid(grid)
        bg,parts=records(grid)
        if not parts:return ['need foreground objects']
        if sum(row.count(bg) for row in grid)<=len(grid)*len(grid[0])//2:return ['background must occupy majority']
    except (ValueError,TypeError) as exc:return [str(exc)]
    return []
