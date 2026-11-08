"""Unroll an induced four-neighbor colored path, or select an anchor-indexed run.

The modal color is background. Start at the reading-order-first endpoint, not
at the first foreground cell. Repeated colors in separated runs stay separate.
Every sampled path has at most 30 cells, keeping the vertical answer ARC-sized.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import groupby
from pathlib import Path
import random

MODES=('straighten','anchor_indexed_run')
RIVALS=('other_setting','row_major','component_row_major','reverse_path','color_sorted',
        'global_color_counts','fixed_first_candidate','fixed_last_candidate','largest_run',
        'smallest_run','modulo_k','anchor_only')
CODE={name:i+1 for i,name in enumerate(RIVALS) if name!='other_setting'}
DELTAS=((-1,0),(1,0),(0,-1),(0,1))


def validate_grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or any(type(row) is not list for row in g):raise ValueError('nonempty row lists with height <=30 required')
    if not 1<=len(g[0])<=30 or any(len(row)!=len(g[0]) for row in g):raise ValueError('rectangular width 1..30 required')
    if any(type(v) is not int or not 0<=v<=9 for row in g for v in row):raise ValueError('exact integer colors 0..9 required')
    return tuple(map(tuple,g))


def _runs(colors):return [list(run) for _,run in groupby(colors)]


def _neighbor_map(cells):
    return {p:sorted((p[0]+dr,p[1]+dc) for dr,dc in DELTAS if (p[0]+dr,p[1]+dc) in cells) for p in cells}


@lru_cache(maxsize=512)
def _analyze(key):
    g=[list(row) for row in key];counts=Counter(v for row in g for v in row)
    bg=min(counts,key=lambda v:(-counts[v],v))
    cells={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg}
    if not 2<=len(cells)<=30:raise ValueError('path must contain 2..30 foreground cells')
    neighbors=_neighbor_map(cells)
    ends=sorted(p for p,n in neighbors.items() if len(n)==1)
    if len(ends)!=2 or any(len(n) not in (1,2) for n in neighbors.values()):raise ValueError('one induced unbranched open four-neighbor path required')
    path=[];prev=None;p=ends[0]
    while True:
        if p in path:raise ValueError('cycle')
        path.append(p);nexts=[q for q in neighbors[p] if q!=prev]
        if not nexts:break
        prev,p=p,nexts[0]
    if len(path)!=len(cells):raise ValueError('disconnected path components')
    colors=[g[r][c] for r,c in path];runs=_runs(colors)
    if len(runs)<2:raise ValueError('at least two color runs required')
    k=len(runs[0]);index=(k-1)%(len(runs)-1)
    return dict(bg=bg,path=path,colors=colors,runs=runs,anchor_length=k,selected_index=index)


def analyze(g):return deepcopy(_analyze(validate_grid(g)))


def _component_colors(g,bg):
    cells={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg};seen=set();colors=[]
    for p in sorted(cells):
        if p in seen:continue
        color=g[p[0]][p[1]];stack=[p];seen.add(p);size=0
        while stack:
            q=stack.pop();size+=1
            for dr,dc in DELTAS:
                n=q[0]+dr,q[1]+dc
                if n in cells and n not in seen and g[n[0]][n[1]]==color:seen.add(n);stack.append(n)
        colors.extend([color]*size)
    return colors


def solve(g,mode='straighten',rival=None):
    if mode not in MODES:raise ValueError('unknown mode')
    z=_analyze(validate_grid(g));colors=list(z['colors'])
    if rival is not None and rival not in RIVALS:raise ValueError('unknown rival')
    if rival=='other_setting':mode=MODES[1-MODES.index(mode)]
    elif rival=='row_major':colors=[v for row in g for v in row if v!=z['bg']]
    elif rival=='component_row_major':colors=_component_colors(g,z['bg'])
    elif rival=='reverse_path':colors=colors[::-1]
    elif rival=='color_sorted':colors=sorted(colors)
    elif rival=='global_color_counts':
        counts=Counter(colors);colors=[v for v in dict.fromkeys(colors) for _ in range(counts[v])]
    runs=_runs(colors);candidates=runs[1:];k=len(runs[0])
    if rival=='anchor_only':answer=runs[0]
    elif rival=='fixed_first_candidate':answer=candidates[0]
    elif rival=='fixed_last_candidate':answer=candidates[-1]
    elif rival=='largest_run':answer=max(candidates,key=len)
    elif rival=='smallest_run':answer=min(candidates,key=len)
    elif rival=='modulo_k':answer=candidates[k%len(candidates)]
    elif mode=='straighten':answer=colors
    else:answer=candidates[(k-1)%len(candidates)]
    return [[v] for v in answer]


def self_check(g):
    try:analyze(g);return []
    except (ValueError,TypeError,IndexError) as e:return [str(e)]


def _rng(seed,tag):return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{tag}'.encode()).digest(),'big'))


def _walk(rng,H,W,n):
    for _ in range(128):
        p=(rng.randrange(H),rng.randrange(W));path=[p];seen={p}
        for i in range(n-1):
            choices=[]
            for dr,dc in DELTAS:
                q=p[0]+dr,p[1]+dc
                if not (0<=q[0]<H and 0<=q[1]<W) or q in seen:continue
                touching={(q[0]+ar,q[1]+ac) for ar,ac in DELTAS}&seen
                if touching=={p}:choices.append(q)
            if not choices:break
            p=rng.choice(choices);path.append(p);seen.add(p)
        if len(path)==n:return path if path[0]<path[-1] else path[::-1]
    raise ValueError('bounded induced-path construction exhausted')


def _scene(seed,tag,stress=False,attempt=0):
    rng=_rng(seed,f'{tag}:{attempt}')
    H,W=(30,30) if stress else rng.choice(((11,13),(13,16),(16,16),(19,21)))
    n=30 if stress else rng.randrange(22,31)
    if stress:
        side=rng.choice((0,29));path=[(r,side) for r in range(30)]
        if rng.randrange(2):path=[(c,r) for r,c in path]
    else:path=_walk(rng,H,W,n)
    nruns=rng.randrange(5,8);lengths=[2]*nruns
    for _ in range(n-2*nruns):lengths[rng.randrange(nruns)]+=1
    bg,*palette=rng.sample(range(10),5);colors=[]
    for i in range(nruns):
        avoid={colors[-1]} if colors else set()
        # Cyclic neighboring candidates differ, so the off-by-one witness cannot collapse.
        if i==nruns-1:avoid.add(colors[1])
        colors.append(rng.choice([c for c in palette if c not in avoid]))
    values=[c for c,length in zip(colors,lengths) for _ in range(length)]
    g=[[bg]*W for _ in range(H)]
    for (r,c),v in zip(path,values):g[r][c]=v
    return g


@lru_cache(maxsize=64)
def _inputs(seed):
    demos=None
    for attempt in range(256):
        grids=[_scene(seed,f'demo:{i}',attempt=attempt) for i in range(2)]
        if all(any(solve(g,mode,rival=rival)!=solve(g,mode) for g in grids)
               for mode in MODES for rival in RIVALS):
            demos=grids;break
    if demos is None:raise ValueError('bounded distinguishing-demo construction exhausted')
    used={validate_grid(g) for g in demos}
    def fresh(tag,stress=False):
        for attempt in range(128):
            g=_scene(seed,tag,stress,attempt);key=validate_grid(g)
            if key not in used and not self_check(g):used.add(key);return g
        raise ValueError('bounded distinct-input construction exhausted')
    demos += [fresh(f'demo:{i}') for i in range(2,6)]
    queries=[fresh(f'query:{i}',i==3) for i in range(4)]
    return demos,queries


def _request(seed,settings,demos,queries):
    if type(seed) is not int or seed<0:raise ValueError('nonnegative integer seed required')
    if type(settings) is not dict or set(settings)!={'mode'} or settings['mode'] not in MODES:raise ValueError('exact mode setting required')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    return settings['mode']


def program(settings):
    mode=_request(0,settings,2,4)
    return Path(__file__).with_name('canonical.rkt' if mode=='straighten' else 'anchor-indexed.rkt').read_text()


def generate(seed,settings,demos,queries):
    mode=_request(seed,settings,demos,queries);ds,qs=_inputs(seed)
    def pair(g):return dict(input=deepcopy(g),output=solve(g,mode))
    return dict(train=[pair(g) for g in ds[:demos]],test=[pair(g) for g in qs[:queries]],program_solution=program(settings))


def present(seed,settings,demos,queries,presentation_seed=0):
    _request(seed,settings,demos,queries)
    if type(presentation_seed) is not int:raise ValueError('integer presentation seed required')
    e=generate(seed,settings,demos,4);order=list(range(4));_rng(seed,f'presentation:{presentation_seed}').shuffle(order)
    views=[{'train':deepcopy(e['train']),'test':[{'input':deepcopy(e['test'][i]['input'])}]} for i in order[:queries]]
    return dict(public=views,private=dict(seed=seed,presentation_seed=presentation_seed,settings=deepcopy(settings),
        source_indices=order[:queries],program=e['program_solution'],source_pairs=deepcopy(e['test'])))


def rival_program(settings,rival):
    mode=_request(0,settings,2,4)
    if rival not in RIVALS:raise ValueError('unknown rival')
    if rival=='other_setting':return program({'mode':MODES[1-MODES.index(mode)]})
    return program(settings).replace('(define rival 0)',f'(define rival {CODE[rival]})')


def counterfactual_program(settings):return rival_program(settings,'modulo_k')


def intermediate(g,settings):
    z=analyze(g); candidates=z['runs'][1:]
    return dict(endpoint=z['path'][0],ordered_run_lengths=[len(r) for r in z['runs']],ordered_run_colors=[r[0] for r in z['runs']],
        anchor_length=z['anchor_length'],selected_index=z['selected_index'],
        wrong_index=z['anchor_length']%len(candidates))


def dependency():
    return dict(step_a='Trace the complete four-neighbor path from its reading-order-first endpoint and segment consecutive color runs; measure the first run length k.',
        intermediate='The ordered subsequent runs and the input-derived selected index (k-1) modulo their count.',
        step_b='Retrieve that selected run from the traced order and emit its color once per run cell as a vertical column.',
        why_b_depends_on_a='Spatial reading order and global color counts lose path order and separate repeated-color runs. The selected run cannot be chosen until tracing supplies both k and the ordered candidates; an off-by-one intermediate selects a different run.')
