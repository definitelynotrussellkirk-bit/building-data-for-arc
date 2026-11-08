"""Legend-controlled periodic trails through a two-color terrain.

Self-contained ordinary generator and diagnostic model. No official labels,
external files or sibling modules are consulted by generation or solving.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import random

GENERATOR_ID=TASK_ID='public_eval_195c6913'
RULE_TASK_ID='ee_195c6913'
VERSION='1.0.0'
EXAMPLES_NEEDED=2
AXES={}
SUMMARY='Trace right/up terrain routes and continue the legend color cycle across bends'
INVARIANTS=['Two aligned 2x2 legends: ordered cycle and lower stop color',
            'Starts are first-cycle-colored singletons on the left edge',
            'Immutable terrain determines routes; generated routes do not overlap']
MODES=('carry','restart')


def grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular 1..30 exact-integer color grid')
    return g


def components(g,bg):
    seen=set();out=[]
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if v==bg or (r,c) in seen:continue
            stack=[(r,c)];seen.add((r,c));cells=[]
            while stack:
                x,y=stack.pop();cells.append((x,y))
                for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
                    q=(x+dx,y+dy)
                    if 0<=q[0]<len(g) and 0<=q[1]<len(row) and q not in seen and g[q[0]][q[1]]==v:
                        seen.add(q);stack.append(q)
            out.append((v,sorted(cells)))
    return out


def parse(g):
    grid(g);bg=g[0][0]
    counts=Counter(v for row in g for v in row if v!=bg)
    if not counts:raise ValueError('Missing terrain and legends')
    terrain=max(counts,key=counts.get)
    if sum(n==counts[terrain] for n in counts.values())!=1:raise ValueError('Terrain must be the unique dominant nonbackground color')
    os=[(v,cs) for v,cs in components(g,bg) if v!=terrain]
    squares=[];single=[]
    for v,cs in os:
        if len(cs)==1:single.append((v,cs[0]));continue
        r=min(x for x,y in cs);c=min(y for x,y in cs)
        if cs!=[(r,c),(r,c+1),(r+1,c),(r+1,c+1)]:raise ValueError('All nonterrain nonsingletons must be exact 2x2 legend blocks')
        squares.append((r,c,v,cs))
    if len(squares)<3:raise ValueError('Missing ordered cycle or stop legend')
    top=min(s[0] for s in squares)
    legend=sorted([s for s in squares if s[0]==top],key=lambda s:s[1])
    stop=[s for s in squares if s[0]!=top]
    cycle=[s[2] for s in legend]
    if not 2<=len(cycle)<=6 or len(set(cycle))<2 or len(stop)!=1 or stop[0][0]<=top+1 or stop[0][2] in cycle:
        raise ValueError('Need an ordered nonconstant cycle and a distinct lower stop-color block')
    if any(b[1]-a[1]<3 for a,b in zip(legend,legend[1:])):raise ValueError('Cycle blocks need a separating column')
    starts=sorted(p for v,p in single if v==cycle[0] and p[1]==0)
    if not 1<=len(starts)<=4 or len(starts)!=len(single):raise ValueError('Only first-color left-edge singleton starts are admitted')
    return dict(bg=bg,terrain=terrain,cycle=cycle,stop=stop[0][2],starts=starts,
                metadata=[p for s in squares for p in s[3]])


def routes(g,*,rival=None):
    """Return immutable-terrain events [kind,row,col,total_index,segment_index].

    kind 0 is a path cell, kind 1 a first obstructing in-bounds cell. The corner
    is visited once; segment_index zero starts on the FIRST CELL AFTER a turn.
    A blocked prospective turn ends the route without an extra collision mark.
    """
    d=parse(g);H,W=len(g),len(g[0]);result=[]
    starts=d['starts'][:1] if rival=='first_start' else d['starts']
    for r,c in starts:
        direction=0;total=local=0;events=[]
        for _ in range(H+W+2):
            events.append([0,r,c,total,local])
            dr,dc=(0,1) if direction==0 else ((1,0) if rival=='down_turn' else (-1,0))
            nr,nc=r+dr,c+dc
            if not (0<=nr<H and 0<=nc<W):break
            if g[nr][nc]==d['terrain']:
                r,c=nr,nc;total+=1;local+=1;continue
            events.append([1,nr,nc,total,local])
            if rival=='straight':break
            direction=1-direction
            dr,dc=(0,1) if direction==0 else ((1,0) if rival=='down_turn' else (-1,0))
            nr,nc=r+dr,c+dc
            if not (0<=nr<H and 0<=nc<W and g[nr][nc]==d['terrain']):break
            r,c=nr,nc;total+=1+(rival=='count_walls');local=0
        else:raise AssertionError('Monotone route exceeded rows+columns bound')
        result.append(events)
    return result


def solve(g,mode='carry',*,rival=None):
    if mode not in MODES:raise ValueError('Unknown phase policy')
    d=parse(g)
    if rival=='identity':return deepcopy(g)
    cycle=d['cycle'][:]
    if rival=='unique_cycle':cycle=list(dict.fromkeys(cycle))
    if rival=='sorted_cycle':cycle=sorted(cycle)
    if rival=='descending_cycle':cycle=sorted(cycle,reverse=True)
    if rival=='reverse_cycle':cycle=cycle[::-1]
    if rival and rival.startswith('period_'):
        n=int(rival.split('_')[1]);cycle=[cycle[i%len(cycle)] for i in range(n)]
    out=deepcopy(g)
    if rival!='keep_legends':
        for r,c in d['metadata']:out[r][c]=d['bg']
    offset=0
    for route in routes(g,rival=rival):
        previous=None
        for kind,r,c,total,local in route:
            if kind==1:
                if rival=='no_markers':continue
                if rival=='mark_last':r,c=previous
                out[r][c]=d['stop']
            else:
                phase=total if mode=='carry' else local
                if rival=='opposite_setting':phase=local if mode=='carry' else total
                if rival=='global_phase':phase+=offset
                out[r][c]=cycle[phase%len(cycle)];previous=(r,c)
        if rival=='global_phase':offset+=sum(e[0]==0 for e in route)
    return out


def rng_for(seed,tag):
    return random.Random(int.from_bytes(hashlib.sha256(f'195c-v1:{seed}:{tag}'.encode()).digest(),'big'))


def _expand(vertices):
    result=[vertices[0]]
    for (r,c),(x,y) in zip(vertices,vertices[1:]):
        if not ((r==x and y>c) or (c==y and x<r)):raise ValueError('Right/up scaffold required')
        dr=0 if r==x else -1;dc=1 if r==x else 0
        while (r,c)!=(x,y):r+=dr;c+=dc;result.append((r,c))
    return result


def scene(seed,index):
    if type(seed) is not int or seed<0 or type(index) is not int or not 0<=index<10:raise ValueError('Nonnegative integer seed and index 0..9 required')
    rng=rng_for(seed,f'input-{index}');H=W=30
    if index!=9:H=rng.randint(22,29);W=rng.randint(22,29)
    colors=rng.sample(range(10),7);bg,terrain,stop=colors[:3];inks=colors[3:]
    if index==0:cycle=sorted(inks[:3],reverse=True)
    elif index==1:
        p,q,r=sorted(inks[:3]);cycle=[p,p,q,r]
    else:
        n=rng.choice((2,3,4)) if index!=9 else 4
        cycle=inks[:n]
        if n>2 and rng.randrange(2):cycle[1]=cycle[0]
    multiple=index in (1,3,7,9);top_exit=index in (2,8)
    c1=rng.randint(4,7);c2=rng.randint(W-8,W-5)
    if multiple:
        r0=H//2;r1=rng.randint(5,7)
        c2=W-5
        if (c2+r0-r1+1)%len(cycle)==0:c2-=1
        vertices=[[(r0,0),(r0,c1),(r1,c1),(r1,c2)],
                  [(H-4,0),(H-4,9),(H//2+3,9),(H//2+3,W-1)]]
        endings=['blocked','edge']
    else:
        r0=H-4;r1=H//2;r2=rng.randint(5,7)
        last=(0,c2) if top_exit else (r2,W-1)
        vertices=[[(r0,0),(r0,c1),(r1,c1),(r1,c2)]+([last] if top_exit else [(r2,c2),last])]
        endings=['edge']
    paths=[_expand(vs) for vs in vertices];reserved=set(p for ps in paths for p in ps)
    if sum(map(len,paths))!=len(reserved):raise AssertionError('Generated paths overlap')
    guards=[];blocked_turn=[]
    for vs,ending in zip(vertices,endings):
        for k,((r,c),(x,y)) in enumerate(zip(vs,vs[1:])):
            dr,dc=(0,1) if r==x else (-1,0)
            q=(x+dr,y+dc)
            if 0<=q[0]<H and 0<=q[1]<W:guards.append((q,dr,dc))
        if ending=='blocked':
            x,y=vs[-1];blocked_turn.append((x-1,y))
    assert not reserved.intersection(q for q,_,_ in guards)
    assert not reserved.intersection(blocked_turn)
    ground=set()
    for ps in paths:
        for r,c in ps:
            radius=rng.randint(3,5) if index==9 else rng.randint(2,4)
            for x in range(max(0,r-radius),min(H,r+radius+1)):
                for y in range(max(0,c-radius),min(W,c+radius+1)):
                    if rng.random()>.08:ground.add((x,y))
    # Carve obstacle rays out to an edge; all reserved trails are restored later.
    for (r,c),dr,dc in guards:
        x,y=r,c
        while 0<=x<H and 0<=y<W:
            ground.discard((x,y))
            if dr==0 and x+1<H:ground.discard((x+1,y))
            if dc==0 and y-1>=0:ground.discard((x,y-1))
            x+=dr;y+=dc
    header_row=1+rng.randrange(2)
    metadata=[]
    for i,color in enumerate(cycle):
        for x in (header_row,header_row+1):
            for y in (1+3*i,2+3*i):metadata.append((x,y,color))
    for x in (H-3,H-2):
        for y in (W-3,W-2):metadata.append((x,y,stop))
    for x in range(header_row+3):
        for y in range(3*len(cycle)+1):ground.discard((x,y))
    for x in range(H-4,H):
        for y in range(W-4,W):ground.discard((x,y))
    ground.update(reserved)
    ground.difference_update(q for q,_,_ in guards);ground.difference_update(blocked_turn);ground.discard((0,0))
    if reserved.intersection((r,c) for r,c,v in metadata):raise AssertionError('Metadata overlaps route')
    g=[[terrain if (r,c) in ground else bg for c in range(W)] for r in range(H)]
    for r,c,color in metadata:g[r][c]=color
    for path in paths:r,c=path[0];g[r][c]=cycle[0]
    d=parse(g)
    actual=[[(e[1],e[2]) for e in route if e[0]==0] for route in routes(g)]
    if actual!=sorted(paths,key=lambda ps:ps[0]):raise AssertionError('Constructive route changed')
    return g


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed) is not int or seed<0 or type(sample_index) is not int or sample_index<0:raise ValueError('Exact nonnegative seed/index required')
    if overrides or difficulty not in (None,'easy','medium','hard'):raise ValueError('No override axes; difficulty must be easy/medium/hard')
    return scene(seed+1000003*(sample_index//10),sample_index%10)


def self_check(g):
    try:parse(g);routes(g)
    except (ValueError,TypeError,IndexError,AssertionError) as exc:return [str(exc)]
    return []
