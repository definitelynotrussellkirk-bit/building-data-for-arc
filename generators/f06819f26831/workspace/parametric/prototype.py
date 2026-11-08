"""Exact completion claims plus largest new-cell gain, with independent Racket authority."""
from __future__ import annotations
from collections import deque
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
HERE=Path(__file__).resolve().parent
MODES=('all_copies','largest_gain')
DIRS=((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1))

def components(g):
    # Match the authority's documented row-major discovery and BFS cell order.
    h,w=len(g),len(g[0]);seen=set();result=[]
    for r in range(h):
        for c in range(w):
            if not g[r][c] or (r,c) in seen:continue
            seen.add((r,c));q=deque([(r,c)]);cells=[]
            while q:
                rr,cc=q.popleft();cells.append((rr,cc))
                for dr,dc in DIRS:
                    nr,nc=rr+dr,cc+dc
                    if 0<=nr<h and 0<=nc<w and g[nr][nc] and (nr,nc) not in seen:
                        seen.add((nr,nc));q.append((nr,nc))
            result.append(cells)
    return result

def canonical(g):
    h,w=len(g),len(g[0]);out=copy.deepcopy(g)
    templates=[cells for cells in components(g) if len({g[r][c] for r,c in cells})>=2]
    protected={p for t in templates for p in t}
    rels=[]
    for cells in templates:
        r0=min(r for r,c in cells);c0=min(c for r,c in cells)
        rels.append([(r-r0,c-c0,g[r][c]) for r,c in cells])
    partials=[(r,c,g[r][c]) for r in range(h) for c in range(w) if g[r][c] and (r,c) not in protected]
    partial_set={(r,c) for r,c,v in partials};seen=set();scored=[]
    for r,c,v in partials:
        for tid,t in enumerate(rels):
            for tr,tc,tv in t:
                if tv!=v:continue
                ro,co=r-tr,c-tc;key=(ro,co,tid)
                # Duplicate candidates have the same score/coverage and cannot
                # change stable greedy order; discard them before expensive checks.
                if key in seen:continue
                seen.add(key)
                cells=[(ro+rr,co+cc,x) for rr,cc,x in t]
                if not all(0<=rr<h and 0<=cc<w and (rr,cc) not in protected and g[rr][cc] in (0,x)
                           for rr,cc,x in cells):continue
                covered={(rr,cc) for rr,cc,x in cells if (rr,cc) in partial_set}
                if covered:scored.append((len(covered),covered,cells))
    scored.sort(key=lambda x:-x[0]);used=set()
    for count,covered,cells in scored:
        if used & covered:continue
        used.update(covered)
        for r,c,v in cells:out[r][c]=v
    return out

def gains(g,stage):
    return [(sum(g[r][c]==0 for r,c in obj),obj) for obj in components(stage)
            if any(g[r][c]==0 for r,c in obj)]

def _finish(g,stage):
    result=copy.deepcopy(stage);items=gains(g,stage)
    if items:
        top=max(n for n,obj in items);winners=[obj for n,obj in items if n==top]
        if len(winners)==1:
            for r,c in winners[0]:result[r][c]=8
    return result

def predict(g,mode):
    if mode not in MODES:raise ValueError('Unknown completion policy')
    stage=canonical(g)
    return stage if mode=='all_copies' else _finish(g,stage)

def intermediate(g):
    stage=canonical(g);items=gains(g,stage)
    rows=[]
    for n,cells in items:
        rows.append({'gain':n,'completed_size':len(cells),'original_cells':len(cells)-n,
                     'bbox':[min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)]})
    return {'completed_objects':rows,'largest_gain':max((x['gain'] for x in rows),default=0)}

def mode_of(settings):
    if type(settings) is not dict or set(settings)!={'completion_policy'} or settings['completion_policy'] not in MODES:
        raise ValueError('Exactly completion_policy=all_copies|largest_gain is required')
    return settings['completion_policy']

def program(settings):
    return (HERE/('canonical.rkt' if mode_of(settings)=='all_copies' else 'alternate.rkt')).read_text()

def _rng(seed,label):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{label}'.encode()).digest(),'big'))

def _template(n,a,b,pose,cut=False):
    secondary={(1,1)} if n<=3 else {(1,1),(1,2)} if n==4 else {(1,1),(1,2),(2,1)}
    cells=[(r,c,b if (r,c) in secondary else a) for r in range(n) for c in range(n)
           if not (cut and (r,c)==(0,n-1))]
    for _ in range(pose%4):cells=[(c,n-1-r,v) for r,c,v in cells]
    if pose//4:cells=[(r,n-1-c,v) for r,c,v in cells]
    return cells

def _scene(seed,index):
    rng=_rng(seed,f'geometry:{index}');stress=index==9;compact=index==6
    h,w=(30,30) if stress else (16,17) if compact else (22+index%4,rng.randint(24,29))
    sizes=([3,4,5] if index in (1,8,9) else [2,3] if compact else [3,4])
    palette=rng.sample([1,2,3,4,5,6,7,9],2*len(sizes))
    templates=[_template(n,palette[2*i],palette[2*i+1],rng.randrange(8),index in (3,7,8))
               for i,n in enumerate(sizes)]
    # Demonstration 1: the larger copy gains more despite a larger partial.
    # Demonstration 2: the small copy gains more despite a much larger template.
    if index==1:
        parts=[(0,'sparse'),(1,'dense'),(2,'dense'),(0,'dense'),(1,'dense')]
    elif index==8:
        parts=[(0,'dense'),(1,'dense'),(2,'sparse'),(0,'sparse'),(2,'dense')]
    else:
        parts=[(0,'sparse'),(1,'sparse'),(0,'dense'),(1,'dense'),(0,'dense')]
    if stress:
        parts=[(0,'sparse'),(1,'sparse'),(2,'dense')]+[(i%3,'dense') for i in range(9)]
    count=4 if stress else 3
    positions=list((i,j) for i in range(count) for j in range(count))
    # Full templates touch opposing corners, so size stress is not empty padding.
    tpos=[positions[0],positions[-1]]
    if len(sizes)==3:tpos.append(positions[count-1])
    free=[q for q in positions if q not in tpos];rng.shuffle(free)
    g=[[0]*w for _ in range(h)]
    def place(cells,n,pos):
        i,j=pos
        r=(h-n) if i==count-1 else round(i*(h-5)/(count-1))
        c=(w-n) if j==count-1 else round(j*(w-5)/(count-1))
        for rr,cc,v in cells:
            if not (0<=r+rr<h and 0<=c+cc<w) or g[r+rr][c+cc]:raise ValueError('Constructive placement failed')
            g[r+rr][c+cc]=v
    for cells,n,pos in zip(templates,sizes,tpos):place(cells,n,pos)
    for (tid,kind),pos in zip(parts,free):
        color=palette[2*tid+(kind=='sparse')]
        cells=[cell for cell in templates[tid] if cell[2]==color]
        place(cells,sizes[tid],pos)
    # Racket remains the authority; construction claims are checked independently.
    return g

@lru_cache(maxsize=4)
def _bank(seed):
    scenes=[_scene(seed,i) for i in range(10)]
    outputs=[]
    for g in scenes:
        stage=canonical(g);outputs.append((stage,_finish(g,stage)))
    return scenes,outputs

def generate(seed,settings,demos,queries):
    mode=mode_of(settings)
    if type(seed) is not int:raise ValueError('seed must be an integer')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    scenes,outputs=_bank(seed)
    order=list(range(6,10));_rng(seed,'presentation').shuffle(order)
    indices=list(range(demos))+order[:queries]
    if len({json.dumps(scenes[i]) for i in indices})!=len(indices):raise ValueError('Duplicate inputs')
    j=MODES.index(mode)
    def pair(i):return {'input':scenes[i],'output':outputs[i][j]}
    return copy.deepcopy({'train':[pair(i) for i in range(demos)],'test':[pair(i) for i in order[:queries]],
                          'program_solution':program(settings)})

def public_view(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('Invalid query index')
    return copy.deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                          'test':[{'input':episode['test'][index]['input']}]})
