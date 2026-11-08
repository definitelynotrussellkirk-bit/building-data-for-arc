"""Remove per-color asymmetry by maximum-support reflection.

The background is the modal color (lower color breaks ties). For each remaining
color, choose the reflection axis retaining the most original cells, then erase
unpaired cells. Lowest doubled axis coordinate breaks score ties. The default
uses vertical axes; the native alternative uses horizontal axes. Coordinates
are doubled integers, so between-cell axes are represented exactly.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from functools import lru_cache
from puzzle_generators.base import gen_ctx

GENERATOR_ID='public_eval_8e5c0c38'
TASK_ID=GENERATOR_ID
RULE_TASK_ID='ee_8e5c0c38'
VERSION='1.0.0'
SUMMARY='Infer a maximum-overlap reflection axis per color and erase unmatched noise.'
EXAMPLES_NEEDED=2
MIN_STRICT_FRAC=1.0
SETTINGS=('vertical','horizontal')
AXES={}
INVARIANTS=['modal background', 'per-color maximal reflection overlap', 'lowest doubled-axis tie break', 'original input determines every reflection pair']

def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value

def validate_grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(x) is not int or not 0<=x<=9 for x in row) for row in g)):
        raise ValueError('expected rectangular 1..30 integer-color grid')
    return g

def background(g):
    validate_grid(g);counts=Counter(v for row in g for v in row)
    return min(counts,key=lambda v:(-counts[v],v))

def _scores(pts,axis,extent):
    lines=defaultdict(list)
    for r,c in pts:
        lines[r if axis=='vertical' else c].append(c if axis=='vertical' else r)
    scores=[0]*(2*extent-1)
    for coords in lines.values():
        for i,x in enumerate(coords):
            scores[2*x]+=1
            for y in coords[i+1:]:scores[x+y]+=2
    return tuple(scores)

@lru_cache(maxsize=128)
def _stats(key):
    counts=Counter(v for row in key for v in row);bg=min(counts,key=lambda v:(-counts[v],v))
    rows=[]
    for color in sorted(set(counts)-{bg}):
        pts=frozenset((r,c) for r,row in enumerate(key) for c,x in enumerate(row) if x==color)
        rows.append((color,pts,_scores(pts,'vertical',len(key[0])),_scores(pts,'horizontal',len(key))))
    return bg,tuple(rows)

def stats(g):
    validate_grid(g);return _stats(tuple(tuple(row) for row in g))

def reflected(p,k,axis):
    r,c=p
    return (r,k-c) if axis=='vertical' else (k-r,c)

def _best(scores,last=False,integers_only=False):
    candidates=range(0,len(scores),2 if integers_only else 1)
    return max(candidates,key=lambda k:(scores[k],k if last else -k))

def best_axis(g,color,axis='vertical'):
    if axis not in SETTINGS:raise ValueError('unknown axis direction')
    _,data=stats(g)
    row=next((r for r in data if r[0]==color),None)
    if row is None:raise ValueError('color must be a non-background input color')
    return _best(row[2 if axis=='vertical' else 3])

def _render(g,bg,data,axis,selector=None,*,fill=False,pairs_only=False):
    out=[row[:] for row in g] if fill else [[bg]*len(g[0]) for _ in g]
    for color,pts,vs,hs in data:
        scores=vs if axis=='vertical' else hs
        k=_best(scores) if selector is None else selector(pts,scores)
        for p in pts:
            q=reflected(p,k,axis)
            if fill:
                if 0<=q[0]<len(g) and 0<=q[1]<len(g[0]):out[q[0]][q[1]]=color
            elif q in pts and (not pairs_only or p!=q):out[p[0]][p[1]]=color
    return out

def solve(g,setting='vertical'):
    if setting not in SETTINGS:raise ValueError('unknown reflection orientation')
    bg,data=stats(g);return _render(g,bg,data,setting)

def _noisy_core(height,width,rng):
    # Two-dimensional non-convex core with parity-dependent half-cell axes.
    # A paired lower spur supports one orientation, but not the other.
    ch=height-4;cw=width-4
    axis=3+cw
    pts={(r,c) for r in range(2,2+ch) for c in range(2,2+cw)
         if r in (2,1+ch) or c in (2,1+cw)}
    lefts=sorted({min(c,axis-c) for c in range(3,1+cw)})
    for r in range(3,1+ch):
        gap=rng.choice(lefts)
        options=[c for c in lefts if c!=gap]
        required=rng.choice(options) if options else None
        for c in options:
            if c==required or rng.random()<0.6:pts|={(r,c),(r,axis-c)}
    pts|={(2+ch,3),(2+ch,cw)}
    # Unpaired connected/outlying additions change the bounding box and means.
    pts|={(2,0),(2,1),(0,1)}
    if rng.randrange(2):pts={(height-1-r,c) for r,c in pts}
    if rng.randrange(2):pts={(r,width-1-c) for r,c in pts}
    return pts

def _tie_core(transpose=False):
    # Six matched pixels on two different axes; lowest-axis outputs differ.
    pts={(0,0),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3),(2,1)}
    return {(c,r) for r,c in pts} if transpose else pts

def scene(seed,index,kind='query'):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    if kind not in ('demo','query'):raise ValueError('kind must be demo or query')
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=GENERATOR_ID+':'+kind)
    rng=ctx.draw_rng('layout')
    if kind=='demo':h,w=((17,19),(19,21),(20,22),(22,24),(24,26),(25,27))[index%6]
    else:h,w=((18,20),(21,23),(26,28),(30,30))[index%4]
    bg,*colors=rng.sample(range(10),5)
    g=[[bg]*w for _ in range(h)]
    hr=(h-1)//2;wc=(w-1)//2
    slots=[(0,0,hr,wc),(0,wc+1,hr,w-wc-1),(hr+1,0,h-hr-1,wc),(hr+1,wc+1,h-hr-1,w-wc-1)]
    rotation=(seed+index)%4;slots=slots[rotation:]+slots[:rotation]
    for profile,((r0,c0,th,tw),color) in enumerate(zip(slots,colors)):
        if profile==0:pts=_noisy_core(th,tw,rng)
        elif profile==1:pts={(c,r) for r,c in _noisy_core(tw,th,rng)}
        else:
            pts=_tie_core(profile==3)
            mh=max(r for r,c in pts)+1;mw=max(c for r,c in pts)+1
            dr=rng.randrange(th-mh+1);dc=rng.randrange(tw-mw+1)
            pts={(r+dr,c+dc) for r,c in pts}
        for r,c in pts:g[r0+r][c0+c]=color
    return g

def generate(seed,sample_index=0,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('invalid difficulty')
    if overrides:raise ValueError('no independent override axes are declared')
    return scene(seed,sample_index,'query')

def self_check(g):
    try:
        bg,data=stats(g)
        if len(data)<2:return ['requires at least two foreground colors']
        if solve(g,'vertical')==g:return ['requires actual removable asymmetry']
        if solve(g,'vertical')==solve(g,'horizontal'):return ['orientation settings must differ']
        return []
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]

def rivals(g,setting):
    bg,data=stats(g);idx=1 if setting=='vertical' else 0
    coords=lambda pts:[p[idx] for p in pts]
    render=lambda selector=None,**kw:_render(g,bg,data,setting,selector,**kw)
    aggregate=[sum(r[2 if setting=='vertical' else 3][k] for r in data) for k in range(2*(len(g[0]) if setting=='vertical' else len(g))-1)]
    common=_best(aggregate)
    return {
        'identity':[row[:] for row in g],
        'opposite_orientation':solve(g,'horizontal' if setting=='vertical' else 'vertical'),
        'bounding_box_midpoint':render(lambda p,s:min(coords(p))+max(coords(p))),
        'whole_grid_midpoint':render(lambda p,s:(len(g[0]) if setting=='vertical' else len(g))-1),
        'coordinate_mean':render(lambda p,s:2*sum(coords(p))//len(p)),
        'coordinate_median':render(lambda p,s:2*sorted(coords(p))[len(p)//2]),
        'integer_axes_only':render(lambda p,s:_best(s,integers_only=True)),
        'last_maximum_axis':render(lambda p,s:_best(s,last=True)),
        'single_global_axis':render(lambda p,s:common),
        'fill_instead_of_erase':render(fill=True),
        'drop_axis_cells':render(pairs_only=True),
    }
