"""Color-band sorting with post-landing component selection.

Self-contained native folder; deterministic Python label claims are checked by
independent protected Racket. Source datasets are never used by the sampler.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
PARAMETERS={'landing_policy':['all_landings','largest_joined']}
DEFAULT={'landing_policy':'all_landings'}
RIVALS=('all_landings','original_largest','most_color','per_band','smallest','first','last','exact_nine','most_pieces')

def _setting(settings):
    if (type(settings) is not dict or set(settings)!=set(PARAMETERS)
            or type(settings['landing_policy']) is not str
            or settings['landing_policy'] not in PARAMETERS['landing_policy']):
        raise ValueError('settings must name exactly one declared landing_policy')
    return settings['landing_policy']

def program(settings):
    policy=_setting(settings);source=(HERE/'canonical.rkt').read_text()
    return source if policy=='all_landings' else source.replace(
        '(define output-policy "all_landings")',f'(define output-policy "{policy}")',1)

def rival_programs():
    source=program(DEFAULT)
    return {name:source.replace('(define output-policy "all_landings")',
        f'(define output-policy "{name}")',1) for name in RIVALS}

def _grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
        or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected rectangular exact-integer 1..30 color grid')
    return tuple(tuple(row) for row in grid)

def components(grid,bg):
    remaining={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg}
    parts=[]
    while remaining:
        first=min(remaining);remaining.remove(first);todo=[first];cells=[first]
        while todo:
            r,c=todo.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in remaining and grid[p[0]][p[1]]==grid[first[0]][first[1]]:
                    remaining.remove(p);todo.append(p);cells.append(p)
        parts.append(sorted(cells))
    return parts

@lru_cache(maxsize=512)
def _analyze(grid):
    h,w=len(grid),len(grid[0]);bg=grid[0][0];bands=[]
    for r,row in enumerate(grid):
        if w>2 and row[0]==row[-1] and row[0]!=row[1] and row[1]!=bg and len(set(row[1:-1]))==1:
            if bands and bands[-1]['end']==r-1 and bands[-1]['color']==row[1]:
                bands[-1]['end']=r
            else:bands.append({'start':r,'end':r,'color':row[1],'rail':row[0]})
    top=bands[0]['start'] if bands else h
    parts=components(grid[:top],bg)
    output=[list(row) for row in grid];mask=[[-1]*w for _ in range(h)];deliveries=[]
    for cells in parts:
        color=grid[cells[0][0]][cells[0][1]]
        band=next((b for b in bands if b['color']==color),None)
        landed=[]
        if band:
            shift=band['end']-max(r for r,c in cells)
            landed=[(r+shift,c) for r,c in cells]
            for r,c in cells:output[r][c]=bg
        deliveries.append({'source':cells,'band':band,'landed':landed})
    for d in deliveries:
        if d['band']:
            for r,c in d['landed']:output[r][c]=mask[r][c]=d['band']['rail']
    return {'output':output,'mask':mask,'groups':components(mask,-1),'deliveries':deliveries,'bands':bands}

def analyze(grid):return deepcopy(_analyze(_grid(grid)))

def predict(grid,policy='all_landings'):
    if policy not in RIVALS+('largest_joined',):raise ValueError('unknown policy')
    info=_analyze(_grid(grid));out=deepcopy(info['output']);parts=info['groups']
    if policy=='all_landings' or not parts:return out
    if policy=='original_largest':selected=max(info['deliveries'],key=lambda d:len(d['source']))['landed']
    elif policy=='most_color':
        mask=info['mask'];colors=sorted({v for row in mask for v in row if v!=-1})
        color=max(colors,key=lambda v:sum(row.count(v) for row in mask))
        selected=[(r,c) for r,row in enumerate(mask) for c,v in enumerate(row) if v==color]
    elif policy=='most_pieces':
        b=max(info['bands'],key=lambda b:sum(d['band']==b for d in info['deliveries']))
        selected=max((p for p in parts if b['start']<=p[0][0]<=b['end']),key=len)
    elif policy=='per_band':
        selected=[]
        for b in info['bands']:
            groups=[p for p in parts if b['start']<=p[0][0] and max(r for r,c in p)<=b['end']]
            if groups:selected+=max(groups,key=len)
    elif policy=='smallest':selected=min(parts,key=len)
    elif policy=='first':selected=parts[0]
    elif policy=='last':selected=parts[-1]
    elif policy=='exact_nine':selected=[p for cells in parts if len(cells)==9 for p in cells]
    else:selected=max(parts,key=len)
    for r,c in selected:out[r][c]=9
    return out

def _scene(seed,index):
    rng=random.Random(f'7c66cb00:geometry:1:{seed}:{index}')
    h=23+index//2;w=26+index%4
    if index==9:h=w=30
    top=h-10
    palette=list(range(9));rng.shuffle(palette)
    bg,a,b,ar,br=palette[:5]
    if index%2:ar,br=b,a
    g=[[bg]*w for _ in range(h)]
    order=[(a,ar),(b,br)] if index%2==0 else [(b,br),(a,ar)]
    for j,(color,rail) in enumerate(order):
        for r in range(top+j*5,top+j*5+4):
            g[r]=[rail]+[color]*(w-2)+[rail]
    n=3+(index%3) # first two lessons: 3 then 4 copies, not a fixed area rule
    shift=rng.randrange(2)
    # Individually separated three-cell Ls become one group at the floor.
    for j in range(n):
        r=1+3*(j%3);c=2+2*j+shift
        for dr,dc in ((0,0),(1,0),(1,1)):g[r+dr][c+dc]=a
    # Largest original object: an eight-cell ring. Its nested one-cell A core
    # must be separated from the ring and sent to a different destination.
    for dr in range(3):
        for dc in range(3):g[1+dr][16+dc]=a if (dr,dc)==(1,1) else b
    # Seven original B pieces compete with 4..6 A pieces. After alignment,
    # duplicate-column singletons merge; B has MORE total paint but no largest
    # connected group. Original object count is deliberately misleading.
    for r in (5,6):
        for c in (w-5,w-4):g[r][c]=b
    for r in (8,9):g[r][w-2]=b
    for r,c in ((0,12),(3,12),(6,13),(10,13)):g[r][c]=b
    if rng.randrange(2):g=[row[::-1] for row in g]
    info=analyze(g);sizes=[len(x) for x in info['groups']]
    if sizes.count(max(sizes))!=1 or max(sizes)!=3*n:
        raise ValueError(f'construction lacks expected unique joined winner: {sizes}')
    return g

@lru_cache(maxsize=128)
def _bank(seed):return tuple(_scene(seed,i) for i in range(10))

def generate(seed,settings,demos=3,queries=4):
    policy=_setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('integer seed, demonstrations 2..6 and queries 1..4 required')
    bank=_bank(seed);permutation=list(range(4));random.Random(f'7c66cb00:presentation:{seed}').shuffle(permutation)
    def pair(i):
        g=deepcopy(bank[i]);return {'input':g,'output':predict(g,policy)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(6+i) for i in permutation[:queries]],
        'program_solution':program(settings),'private':{'seed':seed,'settings':deepcopy(settings),'query_permutation':permutation}}

def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
        'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
