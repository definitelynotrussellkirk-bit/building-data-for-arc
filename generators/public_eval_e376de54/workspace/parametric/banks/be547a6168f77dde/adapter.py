"""Middle-segment normalization and ranking actual boundary-aware cell edits.

The canonical length is positional, not a numerical median. All resources are
local to this native folder. Protected Racket checks the Python claim labels.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
PARAMETERS={'resize_policy':['all_lines','largest_edit']}
DEFAULT={'resize_policy':'all_lines'}
RIVALS=('all_lines','requested_edit','longest_input','shortest_input','growth_only',
        'shrink_only','first_line','last_line','median_length','max_length','largest_rendered','ignore_singletons')


def _setting(settings):
    if (type(settings) is not dict or set(settings)!=set(PARAMETERS)
            or settings.get('resize_policy') not in PARAMETERS['resize_policy']):
        raise ValueError('settings must name exactly one declared resize_policy')
    return settings['resize_policy']


def program(settings):
    policy=_setting(settings);source=(HERE/'canonical.rkt').read_text()
    return source if policy=='all_lines' else source.replace(
        '(define output-policy "all_lines")',f'(define output-policy "{policy}")',1)


def rival_programs():
    source=program(DEFAULT)
    return {k:source.replace('(define output-policy "all_lines")',
                            f'(define output-policy "{k}")',1) for k in RIVALS}


def _grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list
            or not 1<=len(g[0])<=30
            or any(type(row) is not list or len(row)!=len(g[0])
                   or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected rectangular exact-integer color grid, dimensions 1..30')
    return tuple(map(tuple,g))


def _objects(g,bg):
    remaining={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg};lines=[]
    while remaining:
        seed=min(remaining);remaining.remove(seed);todo=[seed];cells=[]
        while todo:
            r,c=todo.pop();cells.append((r,c))
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    p=r+dr,c+dc
                    if p in remaining and g[p[0]][p[1]]==g[r][c]:
                        remaining.remove(p);todo.append(p)
        lines.append({'cells':tuple(sorted(cells)),'color':g[seed[0]][seed[1]]})
    return lines


@lru_cache(maxsize=2048)
def _analyze(g,policy='largest_edit'):
    H,W=len(g),len(g[0]);counts=Counter(v for row in g for v in row)
    bg=min(counts,key=lambda c:(-counts[c],c));lines=_objects(g,bg)
    if not lines or len(lines)%2!=1:raise ValueError('an odd number of parallel segments is required')
    example=next((x['cells'] for x in lines if len(x['cells'])>1),None)
    if example is None:raise ValueError('at least one nonsingleton segment is required')
    dr,dc=example[1][0]-example[0][0],example[1][1]-example[0][1]
    if (dr,dc) not in ((0,1),(1,0),(1,1),(1,-1)):raise ValueError('invalid segment direction')
    for x in lines:
        p=x['cells'][0]
        if x['cells']!=tuple((p[0]+j*dr,p[1]+j*dc) for j in range(len(x['cells']))):
            raise ValueError('segments must be straight and parallel')
    lines.sort(key=lambda x:dr*x['cells'][0][1]-dc*x['cells'][0][0])
    start={dr*x['cells'][0][0]+dc*x['cells'][0][1] for x in lines}
    end={dr*x['cells'][-1][0]+dc*x['cells'][-1][1] for x in lines}
    if len(start)!=1 and len(end)!=1:raise ValueError('segments must share one endpoint baseline')
    forward=len(start)==1;rr,cc=(dr,dc) if forward else (-dr,-dc)
    canonical=len(lines[len(lines)//2]['cells'])
    lengths=sorted(len(x['cells']) for x in lines)
    target=lengths[len(lengths)//2] if policy=='median_length' else max(lengths) if policy=='max_length' else canonical
    out=[[bg]*W for _ in range(H)]
    for x in lines:
        p=x['cells'][0] if forward else x['cells'][-1]
        new=tuple((p[0]+j*rr,p[1]+j*cc) for j in range(target)
                  if 0<=p[0]+j*rr<H and 0<=p[1]+j*cc<W)
        # Independent set difference counts actual additions and deletions.
        x.update(anchor=p,new_cells=new,edits=len(set(new)^set(x['cells'])),
                 requested=abs(target-len(x['cells'])),growth=len(set(new)-set(x['cells'])),
                 shrink=len(set(x['cells'])-set(new)))
        for r,c in new:out[r][c]=x['color']
    return {'background':bg,'lines':lines,'direction':(rr,cc),
            'target':target,'canonical_target':canonical,'normalized':out}


def analyze(g):return deepcopy(_analyze(_grid(g)))


def predict(g,policy='all_lines'):
    if policy not in RIVALS+('largest_edit',):raise ValueError('unknown policy')
    state=_analyze(_grid(g),policy);out=deepcopy(state['normalized']);lines=state['lines']
    if policy=='all_lines':return out
    scores={'requested_edit':lambda x:x['requested'],'longest_input':lambda x:len(x['cells']),
            'shortest_input':lambda x:-len(x['cells']),'growth_only':lambda x:x['growth'],
            'shrink_only':lambda x:x['shrink'],'largest_rendered':lambda x:len(x['new_cells']),
            'ignore_singletons':lambda x:-1 if len(x['cells'])==1 else x['edits']}
    selected=lines[0] if policy=='first_line' else lines[-1] if policy=='last_line' else max(lines,key=scores.get(policy,lambda x:x['edits']))
    for r,c in selected['new_cells']:out[r][c]=8
    return out


def rotate(g,k):
    for _ in range(k%4):g=[list(row) for row in zip(*g[::-1])]
    return g


def _scene(seed,index,attempt=0):
    rng=random.Random(f'e376de54:geometry:v1:{seed}:{index}:{attempt}')
    large=index==9
    if large:
        H=W=30;anchors=[(3*i,5+3*i) for i in range(9)];dr,dc=1,-1
        lengths=[1,9,8,3,12,14,10,8,6]
    elif index==0:
        H,W=rng.randint(20,23),rng.randint(20,23)
        anchors=[(3*i,1+3*i) for i in range(5)];dr,dc=1,-1
        lengths=[1,4,rng.choice([7,8]),1,5]
    elif index==1:
        H,W=rng.randint(23,28),rng.randint(19,26)
        anchors=[(rng.randint(1,3),2+3*i) for i in range(5)]
        # One baseline; do not accidentally sample it separately per segment.
        anchors=[(anchors[0][0],c) for r,c in anchors];dr,dc=1,0
        target=rng.randint(4,7);lengths=[target-1,target+7,target,target+2,target+1]
    else:
        H,W=rng.randint(23,30),rng.randint(23,30)
        n=rng.choice([3,5,7,9]);spacing=rng.choice([2,3])
        if rng.randrange(2):
            n=min(n,7);r0,c0=0,rng.randint(0,3)
            anchors=[(r0+spacing*i,c0+spacing*i) for i in range(n)];dr,dc=1,-1
        else:
            if (n-1)*spacing+2>=W:spacing=2
            anchors=[(rng.randint(0,3),1+spacing*i) for i in range(n)]
            anchors=[(anchors[0][0],c) for r,c in anchors];dr,dc=1,0
        capacities=[min(H-r,c+1) if dc==-1 else H-r for r,c in anchors]
        target=rng.randint(2,min(13,capacities[n//2]))
        lengths=[rng.randint(1,min(16,cap)) for cap in capacities];lengths[n//2]=target
    bg=rng.choice([0,1,5,7,9]);palette=[c for c in range(10) if c not in (bg,8)];rng.shuffle(palette)
    colors=[rng.choice(palette) for _ in lengths]
    g=[[bg]*W for _ in range(H)]
    for (r,c),length,color in zip(anchors,lengths,colors):
        for j in range(length):g[r+j*dr][c+j*dc]=color
    if rng.randrange(2):g=[row[::-1] for row in g]
    g=rotate(g,rng.randrange(4));st=_analyze(_grid(g))
    changes=[x['edits'] for x in st['lines']]
    if len(st['lines'])!=len(lengths) or max(changes)==0 or changes.count(max(changes))!=1:
        raise ValueError('scene lacks a unique actual-edit winner')
    return g


@lru_cache(maxsize=128)
def _bank(seed):
    bank=[];seen=set();survivors=set(RIVALS)-{'all_lines'}
    for index in range(10):
        for attempt in range(120):
            try:g=_scene(seed,index,attempt)
            except ValueError:continue
            key=_grid(g)
            if key in seen:continue
            # Both singleton lines request the same growth, but only one can
            # realize it. Require a visible disagreement with positional tie-break.
            if index==0 and predict(g,'requested_edit')==predict(g,'largest_edit'):continue
            rejected={r for r in survivors if predict(g,r)!=predict(g,'largest_edit')}
            if index==1 and survivors-rejected:continue
            bank.append(g);seen.add(key)
            if index<2:survivors-=rejected
            break
        else:raise ValueError(f'no distinct distinguishing scene at {index}; rivals {sorted(survivors)}')
    if survivors:raise ValueError(f'two-demo survivors {sorted(survivors)}')
    return tuple(bank)


def generate(seed,settings,demos=3,queries=4):
    policy=_setting(settings)
    if (type(seed) is not int or type(demos) is not int or not 2<=demos<=6
            or type(queries) is not int or not 1<=queries<=4):
        raise ValueError('integer seed, demos 2..6 and queries 1..4 required')
    bank=_bank(seed);perm=list(range(4));random.Random(f'e376de54:presentation:{seed}').shuffle(perm)
    def pair(i):
        g=deepcopy(bank[i]);return {'input':g,'output':predict(g,policy)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(6+i) for i in perm[:queries]],
            'program_solution':program(settings),'private':{'seed':seed,'settings':deepcopy(settings),'query_permutation':perm}}


def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
