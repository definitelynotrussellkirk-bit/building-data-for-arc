"""Capacity-limited geodesic collection, with nearest/farthest fixed per lesson.

Fresh randomized mazes; no official grids or answers are imported. A cached
teaching pair contains immutable grids and is independent of requested counts.
All reference labels still require separate protected-Racket execution.
"""
from __future__ import annotations
from collections import deque
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

PARAMETER='collection_order'
VALUES=('nearest','farthest')
DEFAULT={PARAMETER:VALUES[0]}
DEMO_DIMS=((13,15),(14,16),(16,19),(18,22),(22,25),(26,28))
QUERY_DIMS=((12,15),(18,21),(24,27),(30,30))
RIVALS=('opposite_order','identity','ignore_walls','reachable_manhattan',
        'reading_order','capacity_eight','unlimited','preserve_sources',
        'fill_entire_box','reverse_fill','diagonal_paths','euclidean','fixed_center')
DELTAS=((-1,0),(1,0),(0,-1),(0,1))


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid(value):
    if type(value) is not list or not 1<=len(value)<=30 or type(value[0]) is not list or not 1<=len(value[0])<=30:
        raise ValueError('Expected a nonempty grid of at most 30x30')
    if any(type(row) is not list or len(row)!=len(value[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in value):
        raise ValueError('Expected rectangular exact integer colors 0..9')
    return deepcopy(value)


def settings(value):
    if type(value) is not dict or set(value)!={PARAMETER} or type(value[PARAMETER]) is not str or value[PARAMETER] not in VALUES:
        raise ValueError(f'Expected exactly {PARAMETER} in {VALUES}')
    return value[PARAMETER]


def program(setting):
    order=settings(setting);text=Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
    anchor="(define collection-order 'nearest)"
    if text.count(anchor)!=1:raise ValueError('Canonical collection anchor changed')
    return text if order=='nearest' else text.replace(anchor,"(define collection-order 'farthest)")


def distances(g,origin,diagonal=False):
    h,w=len(g),len(g[0]);d={tuple(origin):0};q=deque([tuple(origin)])
    ds=DELTAS+((-1,-1),(-1,1),(1,-1),(1,1)) if diagonal else DELTAS
    while q:
        r,c=q.popleft()
        for dr,dc in ds:
            p=(r+dr,c+dc)
            if 0<=p[0]<h and 0<=p[1]<w and g[p[0]][p[1]]!=6 and p not in d:
                d[p]=d[r,c]+1;q.append(p)
    return d


def derive(g):
    markers=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==2]
    if len(markers)!=1:raise ValueError('Expected exactly one red marker')
    origin=markers[0];d=distances(g,origin)
    slots=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v in (2,3)]
    balls=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==9]
    return {'origin':list(origin),'slots':[list(p) for p in slots],
        'candidates':[{'cell':list(p),'distance':d[p],
                       'manhattan':abs(p[0]-origin[0])+abs(p[1]-origin[1]),
                       'squared':(p[0]-origin[0])**2+(p[1]-origin[1])**2} for p in balls if p in d],
        'unreachable':[list(p) for p in balls if p not in d]}


def solve(value,order='nearest',*,rival=None):
    g=grid(value)
    if type(order) is not str or order not in VALUES:raise ValueError('Unknown collection order')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    state=derive(g);out=deepcopy(g);origin=state['origin'];slots=state['slots']
    if rival=='identity':return out
    if rival=='opposite_order':order=VALUES[1-VALUES.index(order)]
    candidates=state['candidates']
    if rival in ('ignore_walls','diagonal_paths','fixed_center'):
        start=(len(g)//2,len(g[0])//2) if rival=='fixed_center' else tuple(origin)
        d=distances(g,start,diagonal=rival=='diagonal_paths')
        candidates=[]
        for r,row in enumerate(g):
            for c,v in enumerate(row):
                if v!=9:continue
                if rival=='ignore_walls':dist=abs(r-origin[0])+abs(c-origin[1])
                elif (r,c) in d:dist=d[r,c]
                else:continue
                candidates.append({'cell':[r,c],'distance':dist})
    metric='manhattan' if rival=='reachable_manhattan' else 'squared' if rival=='euclidean' else 'distance'
    def key(record):
        r,c=record['cell']
        if rival=='reading_order':return (r,c)
        distance=record[metric]
        return (distance if order=='nearest' else -distance,r,c)
    ranked=sorted(candidates,key=key)
    capacity=len(slots)-(1 if rival=='capacity_eight' else 0)
    selected=ranked if rival=='unlimited' else ranked[:capacity]
    if rival!='preserve_sources':
        for record in selected:
            r,c=record['cell'];out[r][c]=7
    if rival=='reverse_fill':slots=slots[::-1]
    count=len(slots) if rival=='fill_entire_box' else min(len(slots),len(selected))
    for r,c in slots[:count]:out[r][c]=9
    return out


def input_errors(value):
    try:
        g=grid(value);state=derive(g)
    except (ValueError,TypeError,IndexError) as error:return [str(error)]
    if any(v not in (2,3,6,7,9) for r in g for v in r):return ['Unknown maze role color']
    r,c=state['origin'];expected={(r+dr,c+dc) for dr in (-1,0,1) for dc in (-1,0,1)}
    if {tuple(p) for p in state['slots']}!=expected:return ['Expected one complete centered 3x3 destination']
    ds=sorted(record['distance'] for record in state['candidates'])
    if len(ds)>9 and (ds[8]==ds[9] or ds[-10]==ds[-9]):return ['Selection cutoff has an unlearned distance tie']
    return []


def sample(seed,stream,index,attempt=0):
    integer(seed,0,2**63-1,'seed');integer(attempt,0,4095,'attempt')
    if stream not in ('demo','query'):raise ValueError('Unknown stream')
    dims=DEMO_DIMS if stream=='demo' else QUERY_DIMS;integer(index,0,len(dims)-1,'index')
    h,w=dims[index];rng=random.Random(f'collection-v1:{seed}:{stream}:{index}:{attempt}')
    g=[[6]*w for _ in range(h)]
    nodes={(r,c) for r in range(1,h-1,2) for c in range(1,w-1,2)}
    start=rng.choice(sorted(nodes));stack=[start];visited={start};g[start[0]][start[1]]=7
    while stack:
        r,c=stack[-1]
        ns=[(r+2*dr,c+2*dc) for dr,dc in DELTAS if (r+2*dr,c+2*dc) in nodes-visited]
        if not ns:stack.pop();continue
        nr,nc=rng.choice(ns);g[(r+nr)//2][(c+nc)//2]=7;g[nr][nc]=7
        visited.add((nr,nc));stack.append((nr,nc))
    # A small number of loops complements tree corridors and long detours.
    for r in range(1,h-1):
        for c in range(1,w-1):
            if g[r][c]==6 and rng.random()<0.06 and ((g[r-1][c]!=6 and g[r+1][c]!=6) or (g[r][c-1]!=6 and g[r][c+1]!=6)):
                g[r][c]=7
    centers=[(r,c) for r in range(3,h-3,2) for c in range(3,w-3,2) if (r,c)!=(h//2,w//2)]
    cr,cc=rng.choice(centers)
    # Connected exits reach each physical boundary; sealed corner tokens remain
    # out of reach under cardinal movement but catch diagonal/no-wall shortcuts.
    tc=rng.choice(list(range(3,w-3,2)));br=rng.choice(list(range(3,h-3,2)))
    for r in (0,1):g[r][tc]=7
    for r in (h-3,h-2,h-1):g[r][tc]=7
    for c in (0,1):g[br][c]=7
    for c in (w-3,w-2,w-1):g[br][c]=7
    for r,c in ((0,0),(0,w-1),(h-1,0),(h-1,w-1)):g[r][c]=9
    # Paint the destination after exit carving: an exit may intersect its bbox.
    for dr in (-1,0,1):
        for dc in (-1,0,1):g[cr+dr][cc+dc]=3
    g[cr][cc]=2
    count=(18,24,32,45)[index] if stream=='query' else (18,rng.randint(4,7),9,0,20,24)[index]
    # At least one genuinely interior sealed token prevents 'only corners are
    # unreachable' from describing the sampled topology. Trial a local pocket
    # without destroying the target or the required reachable sampling capacity.
    pockets=[(r,c) for r in range(2,h-2) for c in range(2,w-2)
             if g[r][c] in (6,7) and all(g[r+dr][c+dc] in (6,7) for dr,dc in DELTAS)]
    rng.shuffle(pockets)
    for r,c in pockets:
        trial=deepcopy(g);trial[r][c]=9
        for dr,dc in DELTAS:trial[r+dr][c+dc]=6
        reach=distances(trial,(cr,cc))
        if sum(trial[a][b]==7 for a,b in reach)>=count+5:
            g=trial;break
    else:raise ValueError('No safe interior pocket in bounded maze')
    d=distances(g,(cr,cc));floor=[p for p in sorted(d) if g[p[0]][p[1]]==7]
    if len(floor)<count:raise ValueError('Maze lacks enough reachable floor')
    for _ in range(512):
        balls=rng.sample(floor,count);scores=sorted(d[p] for p in balls)
        if count<=9 or (scores[8]<scores[9] and scores[-10]<scores[-9]):break
    else:raise ValueError('Bounded sampler could not separate distance cutoffs')
    for r,c in balls:g[r][c]=9
    errors=input_errors(g)
    if errors:raise ValueError('; '.join(errors))
    return g


@lru_cache(maxsize=64)
def teaching(seed):
    for attempt in range(128):
        pair=[sample(seed,'demo',i,attempt) for i in range(2)]
        if all(survivors([{'input':g,'output':solve(g,value)} for g in pair],{PARAMETER:value})==['intended'] for value in VALUES):
            return tuple(tuple(tuple(row) for row in g) for g in pair)
    raise ValueError('Bounded teaching search could not refute the declared rivals')


def generate(seed,setting,demos,queries):
    integer(seed,0,2**63-1,'seed');order=settings(setting)
    integer(demos,2,6,'demos');integer(queries,1,4,'queries')
    first=[list(map(list,g)) for g in teaching(seed)]
    inputs=first+[sample(seed,'demo',i) for i in range(2,demos)]
    query_inputs=[sample(seed,'query',i) for i in range(queries)]
    pairs=lambda gs:[{'input':g,'output':solve(g,order)} for g in gs]
    return {'train':pairs(inputs),'test':pairs(query_inputs),'program_solution':program(setting)}


def survivors(train,setting):
    order=settings(setting);result=['intended']
    for name in RIVALS:
        if all(solve(p['input'],order,rival=name)==p['output'] for p in train):result.append(name)
    return result


def public_view(episode,query_index):
    integer(query_index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':grid(p['input']),'output':grid(p['output'])} for p in episode['train']],
            'test':[{'input':grid(episode['test'][query_index]['input'])}]}


def presentation_order(presentation_seed):
    integer(presentation_seed,0,2**63-1,'presentation seed')
    order=list(range(4));random.Random(f'collection-presentation-v1:{presentation_seed}').shuffle(order);return order


def public_turns(seed,setting,demos,presentation_seed=0,count=4):
    integer(count,1,4,'presentation count');episode=generate(seed,setting,demos,4)
    integer(presentation_seed,0,2**63-1,'presentation seed')
    return [public_view(episode,i) for i in presentation_order(seed ^ presentation_seed)[:count]]
