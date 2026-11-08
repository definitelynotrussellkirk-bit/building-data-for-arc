"""Four-arm spiral completion and post-clipping fragment selection.

Pure standard-library sampler. Python labels are claims, independently replayed
by protected Racket. No original dataset or sibling checkout is consulted.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
PARAMETERS = {'spiral_policy': ['all_paths', 'longest_fragment']}
DEFAULT = {'spiral_policy': 'all_paths'}
RIVALS = ('all_paths', 'smallest', 'first', 'last', 'bbox', 'north_seed', 'whole_arm')


def _setting(settings):
    if (type(settings) is not dict or set(settings) != set(PARAMETERS)
        or type(settings['spiral_policy']) is not str
        or settings['spiral_policy'] not in PARAMETERS['spiral_policy']):
        raise ValueError('settings must name exactly one declared spiral_policy')
    return settings['spiral_policy']


def program(settings):
    policy = _setting(settings)
    source = (HERE / 'canonical.rkt').read_text()
    return source if policy == 'all_paths' else source.replace(
        '(define output-policy "all_paths")', f'(define output-policy "{policy}")', 1)


def rival_programs():
    source = program(DEFAULT)
    return {name: source.replace('(define output-policy "all_paths")',
        f'(define output-policy "{name}")', 1) for name in RIVALS}


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row) != len(grid[0])
        or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError('expected rectangular exact-integer 1..30 color grid')
    return tuple(tuple(row) for row in grid)


def components(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0}
    parts = []
    while remaining:
        start = min(remaining); remaining.remove(start); todo = [start]; cells = [start]
        while todo:
            r, c = todo.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in remaining and grid[p[0]][p[1]] == grid[start[0]][start[1]]:
                    remaining.remove(p); todo.append(p); cells.append(p)
        parts.append(sorted(cells))
    return parts


@lru_cache(maxsize=2048)
def _analyze(grid):
    height, width = len(grid), len(grid[0])
    seeds = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    if not seeds: raise ValueError('missing spokes')
    colors = {grid[r][c] for r,c in seeds}
    if len(colors) != 1 or 2 in colors: raise ValueError('spokes need one nonzero non-red color')
    rmin,rmax = min(r for r,c in seeds), max(r for r,c in seeds)
    cmin,cmax = min(c for r,c in seeds), max(c for r,c in seeds)
    if (rmax-rmin)%2 or (cmax-cmin)!=(rmax-rmin): raise ValueError('unequal spoke extents')
    cr,cc = (rmin+rmax)//2,(cmin+cmax)//2
    raw_radius = (rmax-rmin)//2
    dirs = ((-1,0),(0,1),(1,0),(0,-1))
    expected = {(cr+dr*t,cc+dc*t) for dr,dc in dirs for t in range(1,raw_radius+1)}
    if raw_radius < 1 or seeds != expected: raise ValueError('expected four complete equal spokes and an empty center')
    radius = max(2,raw_radius)
    arms = []
    # Independent pointwise tracer: includes off-canvas motion but stores only
    # visible coordinates. The Racket rule constructs complete line segments.
    for dr,dc in dirs:
        r,c = cr,cc; cells=[]
        def move(n,er,ec):
            nonlocal r,c
            for _ in range(n):
                r += er; c += ec
                if 0 <= r < height and 0 <= c < width: cells.append((r,c))
        move(radius,dr,dc);dr,dc=dc,-dr
        for k in range(max(height,width)):
            move(4*k+2,dr,dc);er,ec=dc,-dr
            move(radius-2,er,ec);move(radius,dr,dc);dr,dc=er,ec
        arms.append(cells)
    color=next(iter(colors));out=[list(row) for row in grid]
    for cells in arms:
        for r,c in cells:out[r][c]=color
    return {'output':out,'groups':components(out),'arms':arms,
        'center':[cr,cc],'radius':raw_radius,'color':color}


def analyze(grid): return deepcopy(_analyze(_grid(grid)))


def _select(info,policy):
    groups=info['groups']
    if policy=='all_paths': return []
    if policy=='smallest': return min(groups,key=len)
    if policy=='first': return groups[0]
    if policy=='last': return groups[-1]
    if policy=='bbox':
        return max(groups,key=lambda x:(max(r for r,c in x)-min(r for r,c in x)+1)*(max(c for r,c in x)-min(c for r,c in x)+1))
    if policy=='north_seed':
        cr,cc=info['center'];return next(x for x in groups if (cr-1,cc) in x)
    if policy=='whole_arm': return max(info['arms'],key=len)
    return max(groups,key=len)


def predict(grid,policy='all_paths'):
    if policy not in RIVALS+('longest_fragment',):raise ValueError('unknown policy')
    info=_analyze(_grid(grid));out=deepcopy(info['output'])
    for r,c in _select(info,policy):out[r][c]=2
    return out


def _candidate(rng,index):
    h,w=(30,30) if index==9 else (rng.randint(12,29),rng.randint(12,29))
    radius=rng.randint(1,min(6,(min(h,w)-3)//2))
    cr=rng.randint(radius,h-radius-1);cc=rng.randint(radius,w-radius-1)
    color=rng.choice((1,3,4,5,6,7,8,9))
    g=[[0]*w for _ in range(h)]
    for dr,dc in ((-1,0),(0,1),(1,0),(0,-1)):
        for t in range(1,radius+1):g[cr+dr*t][cc+dc*t]=color
    return g


@lru_cache(maxsize=128)
def _bank(seed):
    bank=[];seen=set();remaining=set(RIVALS)-{'all_paths'}
    for index in range(10):
        rng=random.Random(f'da515329:geometry:1:{seed}:{index}')
        best=None;best_rejected=set()
        for attempt in range(160):
            g=_candidate(rng,index);key=tuple(map(tuple,g))
            if key in seen:continue
            info=_analyze(key);sizes=[len(x) for x in info['groups']]
            if sizes.count(max(sizes))!=1:continue
            target=set(_select(info,'longest_fragment'))
            rejected={name for name in remaining if set(_select(info,name))!=target}
            if index>=2 or rejected==remaining:
                best=g;best_rejected=rejected;break
            if best is None or len(rejected)>len(best_rejected):best=g;best_rejected=rejected
        if best is None:raise ValueError(f'no unique fragment scene at {index}')
        if index<2:remaining-=best_rejected
        bank.append(best);seen.add(tuple(map(tuple,best)))
    if remaining:raise ValueError(f'two demos fail to reject {sorted(remaining)}')
    return tuple(bank)


def generate(seed,settings,demos=3,queries=4):
    policy=_setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('integer seed, demonstrations 2..6 and queries 1..4 required')
    bank=_bank(seed);permutation=list(range(4));random.Random(f'da515329:presentation:{seed}').shuffle(permutation)
    def pair(i):
        g=deepcopy(bank[i]);return {'input':g,'output':predict(g,policy)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(6+i) for i in permutation[:queries]],
        'program_solution':program(settings),'private':{'seed':seed,'settings':deepcopy(settings),'query_permutation':permutation}}


def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
        'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
