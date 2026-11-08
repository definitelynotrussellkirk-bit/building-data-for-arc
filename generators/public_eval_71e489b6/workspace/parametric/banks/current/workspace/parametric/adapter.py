"""Binary defect cleanup and orange-rim selection; private authoring adapter.

No official puzzles are read at generation time. Python outputs are claims:
preflight/audit independently execute the stored Racket programs.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ('all_rims', 'largest_rim')
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
EIGHT = tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if (r,c)!=(0,0))


def integer(x, lo, hi, name):
    if type(x) is not int or not lo <= x <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return x


def grid(g, *, binary=False):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
            or not 1 <= len(g[0]) <= 30 or any(type(row) is not list or len(row)!=len(g[0])
            or any(type(x) is not int or x not in (range(2) if binary else range(10)) for x in row) for row in g)):
        raise ValueError('expected a rectangular 1..30 exact-integer grid')
    return g


def setting(settings):
    if type(settings) is not dict or set(settings)!={'selection'} or type(settings['selection']) is not str or settings['selection'] not in MODES:
        raise ValueError('settings must name exactly one declared selection')
    return settings['selection']


def program(settings):
    return (HERE / ('canonical.rkt' if setting(settings)=='all_rims' else 'largest_rim.rkt')).read_text()


def neighbors(p, h, w, deltas=CARDINAL):
    r,c=p
    return [(r+dr,c+dc) for dr,dc in deltas if 0<=r+dr<h and 0<=c+dc<w]


def components(cells, deltas=CARDINAL):
    todo=set(cells);out=[]
    while todo:
        start=min(todo);todo.remove(start);stack=[start];obj={start}
        while stack:
            r,c=stack.pop()
            for dr,dc in deltas:
                p=(r+dr,c+dc)
                if p in todo:todo.remove(p);stack.append(p);obj.add(p)
        out.append(obj)
    return out


def has_core(cells):
    return any({(r,c),(r+1,c),(r,c+1),(r+1,c+1)} <= cells for r,c in cells)


def analyze(g):
    """Detection uses the ORIGINAL grid, not the cleaned intermediate."""
    grid(g,binary=True);h,w=len(g),len(g[0])
    colors={v:{(r,c)for r in range(h)for c in range(w)if g[r][c]==v}for v in (0,1)}
    stray=set().union(*(obj for obj in components(colors[1]) if not has_core(obj)))
    stray.update(p for p in colors[1] if sum(q in colors[1] for q in neighbors(p,h,w))<=1)
    holes=set().union(*(obj for obj in components(colors[0]) if not has_core(obj)))
    for p in colors[0]:
        adjacent=neighbors(p,h,w);blue=sum(q in colors[1] for q in adjacent)
        if blue>=3 or blue==len(adjacent):holes.add(p)
    clean=[row[:] for row in g]
    for r,c in stray:clean[r][c]=0
    rim=set().union(*(set(neighbors(p,h,w,EIGHT)) for p in holes))-holes
    return clean,holes,rim


def solve(g, mode='all_rims'):
    if mode not in MODES:raise ValueError('unknown selection mode')
    clean,holes,rim=analyze(g)
    if mode=='largest_rim' and rim:
        rim=max(components(rim),key=len)  # ordered discovery => row-major ties
    for r,c in rim:clean[r][c]=7
    return clean


def counterfactual(g):
    """Wrong order: choose the largest black defect BEFORE drawing/merging rims."""
    clean,holes,_=analyze(g);h,w=len(g),len(g[0])
    selected=max(components(holes),key=len) if holes else set()
    rim=set().union(*(set(neighbors(p,h,w,EIGHT))for p in selected))-holes
    for r,c in rim:clean[r][c]=7
    return clean


def rng_for(seed, label):
    from puzzle_generators.base import gen_ctx
    return gen_ctx(seed=seed,sample_index=0,version='1.0.0',task_id='public_eval_71e489b6').draw_rng(label)


def rotate(g, n):
    for _ in range(n%4):g=[list(row)for row in zip(*g[::-1])]
    return g


def scene(seed, index):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    rng=rng_for(seed,f'scene:{index}')
    stress=index==9
    small=index in (6,7,8)
    h,w=(30,30) if stress else ((22,22) if index==1 else (16,16) if index==6 else (rng.randint(16,19),rng.randint(16,19)) if small else (rng.randint(22,29),rng.randint(22,29)))
    g=[[1]*w for _ in range(h)]
    # A large structural zero reservoir, a narrow channel, and isolated blue noise.
    for r in range(h-6,h):
        for c in range(w-6,w):g[r][c]=0
    for r in range(h-8 if index==1 else h-11,h-6):g[r][w-4]=0
    g[h-4][w-6]=1               # attached one-neighbor blue tip
    g[h-2][w-2]=1               # disconnected blue impulse
    if index%2:g[h-2][w-3]=1   # a disconnected 2-cell impulse
    # Interior 3x3 structural cavity: not every enclosed black region is a defect.
    for r in range(h//2-1,h//2+2):
        for c in range(w-9,w-6):g[r][c]=0
    # Two separated tiny defects whose rims join and outweigh a larger defect.
    a=(rng.randint(2,4),rng.randint(2,4))
    for r,c in (a,(a[0],a[1]+3)):g[r][c]=0
    if index%3==2:g[a[0]+3][a[1]]=0
    b=(h//2+rng.randint(0,1),rng.randint(2,4))
    shape = tuple((0,k) for k in range(5)) if index%3==0 else ((0,0),(1,0),(1,1))
    for dr,dc in shape:g[b[0]+dr][b[1]+dc]=0
    # Distinct dents, clipped corners, diagonal defects, and sparse nonwinning rims.
    g[0][w//2]=0;g[h-1][3]=0
    if index==1:
        for r,c in ((2,11),(5,14),(8,17)):g[r][c]=0
    elif index%3==1:
        g[4][w-5]=0;g[7][w-2]=0  # rims touch only diagonally
    else:g[3][w-3]=0
    if index%3==2:g[0][0]=0
    # Extra query structure changes components/counts instead of only recoloring.
    if index>=6:
        for r,c in ((h-5,3),(h-5,6)) if index%2 else ((h-5,3),):g[r][c]=0
    if rng.randrange(2):g=[row[::-1]for row in g]
    n=(0 if index==0 else 2 if index==1 else rng.randrange(4))
    g=rotate(g,n)
    if index in (1,8):
        # A bounded blue island in a majority-black field, as in the parent.
        h,w=len(g),len(g[0]);canvas=[[0]*30 for _ in range(30)]
        r0=(30-h)//2;c0=(30-w)//2
        for r in range(h):canvas[r0+r][c0:c0+w]=g[r][:]
        canvas[1][1]=1;canvas[28][28]=1
        g=canvas
    return g


def generate(seed, settings, demos=3, queries=4):
    integer(seed,0,2**63-1,'seed');integer(demos,2,6,'demos');integer(queries,1,4,'queries')
    mode=setting(settings)
    def pair(i):
        g=scene(seed,i);return {'input':g,'output':solve(g,mode)}
    return {'train':[pair(i)for i in range(demos)],'test':[pair(i)for i in range(6,6+queries)],
            'program_solution':program(settings),'settings':dict(settings),'seed':seed}


def query_order(presentation_seed=0):
    integer(presentation_seed,0,2**63-1,'presentation_seed')
    order=list(range(4));rng_for(presentation_seed,'presentation').shuffle(order);return order


def public_turn(episode, turn, *, presentation_seed=0):
    integer(turn,0,3,'turn')
    if type(episode) is not dict or type(episode.get('test')) is not list or len(episode['test'])!=4:
        raise ValueError('project from the complete four-query private bank')
    if type(episode.get('train')) is not list or not 2<=len(episode['train'])<=6:raise ValueError('invalid demonstrations')
    idx=query_order(presentation_seed)[turn]
    return copy.deepcopy({'train':[{'input':grid(p['input']),'output':grid(p['output'])}for p in episode['train']],
                         'test':[{'input':grid(episode['test'][idx]['input'])}]})


def rival(g, name):
    clean,holes,rim=analyze(g);h,w=len(g),len(g[0])
    if name in MODES:return solve(g,name)
    if name=='largest_defect_first':return counterfactual(g)
    if name=='identity':return copy.deepcopy(g)
    if name=='clean_only':return clean
    if name=='keep_noise':clean=[row[:]for row in g]
    elif name=='four_neighbor_rim':rim=set().union(*(set(neighbors(p,h,w))for p in holes))-holes
    elif name=='ignore_dents':
        holes={p for obj in components({(r,c)for r in range(h)for c in range(w)if g[r][c]==0}) if not has_core(obj) for p in obj}
        rim=set().union(*(set(neighbors(p,h,w,EIGHT))for p in holes))-holes
    elif name=='paint_defects':rim|=holes
    elif name=='all_zero_rims':
        zeros={(r,c)for r in range(h)for c in range(w)if g[r][c]==0}
        rim=set().union(*(set(neighbors(p,h,w,EIGHT))for p in zeros))-zeros
    elif name=='clean_then_detect':
        _,_,rim=analyze(clean)
    elif name in ('first_rim','last_rim','smallest_rim','largest_bbox','eight_connected_largest'):
        objs=components(rim,EIGHT if name=='eight_connected_largest' else CARDINAL)
        if not objs:return clean
        if name=='first_rim':rim=objs[0]
        elif name=='last_rim':rim=objs[-1]
        elif name=='smallest_rim':rim=min(objs,key=len)
        elif name=='largest_bbox':rim=max(objs,key=lambda o:(max(r for r,c in o)-min(r for r,c in o)+1)*(max(c for r,c in o)-min(c for r,c in o)+1))
        else:rim=max(objs,key=len)
    else:
        if name not in ('keep_noise',):raise ValueError(name)
    for r,c in rim:clean[r][c]=7
    return clean

RIVALS=MODES+('largest_defect_first','identity','clean_only','keep_noise','four_neighbor_rim','ignore_dents',
              'paint_defects','all_zero_rims','clean_then_detect','first_rim','last_rim','smallest_rim','largest_bbox','eight_connected_largest')


def causal_intermediate(g):
    _,_,rim=analyze(g);groups=components(rim)
    selected=max(groups,key=len) if groups else set()
    return {'orange_component_sizes':list(map(len,groups)),
            'selected_size':len(selected),'selected_first_cell':list(min(selected))if selected else None}
