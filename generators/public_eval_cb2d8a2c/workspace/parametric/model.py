"""Constructive count-controlled routing. No official records or labels are read."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from pathlib import Path
import hashlib
import random

BASE=Path(__file__).resolve().parent
OPTIONS=('full_route','longest_bypass')


def rng_for(seed: int, tag: str) -> random.Random:
    return random.Random(int.from_bytes(hashlib.sha256(f'cb2d8a2c-v1|{seed}|{tag}'.encode()).digest(),'big'))


def rotate(g, turns):
    out=deepcopy(g)
    for _ in range(turns%4):out=[list(row) for row in zip(*out[::-1])]
    return out


def inspect(g, *, clearance_fixed=None, margin=1):
    h,w=len(g),len(g[0])
    sources=[(r,c) for r in range(h) for c in range(w) if g[r][c]==3]
    if len(sources)!=1:raise ValueError('Exactly one green boundary source is required')
    r,c=sources[0]
    if r==0:turns=0
    elif c==0:turns=1
    elif r==h-1:turns=2
    elif c==w-1:turns=3
    else:raise ValueError('Source must lie on a boundary')
    t=rotate(g,turns);H,W=len(t),len(t[0])
    sr,sc=next((r,c) for r in range(H) for c in range(W) if t[r][c]==3)
    bg=Counter(v for row in t for v in row).most_common(1)[0][0]
    walls=[];legs=[];x=sc
    for row in range(H):
        occupied=[c for c in range(W) if t[row][c] in (1,2)]
        if not occupied:continue
        lo,hi=min(occupied),max(occupied)
        n=sum(t[row][c]==1 for c in occupied)
        d=n+margin if clearance_fixed is None else clearance_fixed
        target=hi+d if lo==0 else lo-d
        walls.append(dict(row=row,start=lo,end=hi,markers=n,width=len(occupied),clearance=d))
        legs.append(dict(row=row-d,from_column=x,to_column=target,length=abs(target-x)+1,
                         wall_index=len(walls)-1,markers=n,width=len(occupied)))
        x=target
    winner=max(range(len(legs)),key=lambda i:legs[i]['length']) if legs else None
    return dict(background=bg,rotation=turns,normalized=t,source=[sr,sc],walls=walls,legs=legs,winner=winner)


def solve(g, scope='full_route', *, rival=None):
    if scope not in OPTIONS:raise ValueError('Unknown trace scope')
    fixed={'clearance_one':1,'clearance_two':2}.get(rival)
    margin=0 if rival=='count_without_margin' else 1
    try:f=inspect(g,clearance_fixed=fixed,margin=margin)
    except ValueError:return deepcopy(g)
    t=f['normalized'];H,W=len(t),len(t[0]);sr,sc=f['source'];legs=f['legs']
    out=[[2 if v==1 else v for v in row] for row in t]
    def paint(cells):
        for r,c in cells:
            if 0<=r<H and 0<=c<W:out[r][c]=3
    def cross(leg):
        a,b=sorted((leg['from_column'],leg['to_column']))
        return [(leg['row'],c) for c in range(a,b+1)]
    forced=('first_bypass','last_bypass','largest_marker_count','widest_wall','start_relative_span')
    if rival in forced:scope='longest_bypass'
    if scope=='full_route':
        row,col=sr,sc
        for leg in legs:
            a,b=sorted((row,leg['row']))
            paint((r,col) for r in range(a,b+1));paint(cross(leg))
            row,col=leg['row'],leg['to_column']
        paint((r,col) for r in range(row,H))
    elif legs:
        if rival=='first_bypass':winner=0
        elif rival=='last_bypass':winner=len(legs)-1
        elif rival=='largest_marker_count':winner=max(range(len(legs)),key=lambda i:legs[i]['markers'])
        elif rival=='widest_wall':winner=max(range(len(legs)),key=lambda i:legs[i]['width'])
        elif rival=='start_relative_span':winner=max(range(len(legs)),key=lambda i:abs(legs[i]['to_column']-sc))
        else:winner=f['winner']
        paint(cross(legs[winner]))
    return rotate(out,-f['rotation'])


def validate(settings):
    if type(settings) is not dict or set(settings)!={'trace_scope'} or settings['trace_scope'] not in OPTIONS:
        raise ValueError('settings must be exactly trace_scope=full_route|longest_bypass')
    return settings['trace_scope']


def program(settings):
    scope=validate(settings)
    return (BASE/('canonical.rkt' if scope=='full_route' else 'longest.rkt')).read_text()


def scene(rng, index):
    """Construct edge-attached walls with legal clearances, not output-filtered grids."""
    if type(index) is not int or not 0<=index<10:raise ValueError('scene index must be 0..9')
    for _ in range(100):
        W=30 if index==9 else rng.randint(22,30)
        if index==0:
            source=W-12;targets=[W-4,6,W-7];counts=[3,1,0]
        elif index==1:
            source=W-10;targets=[6,W-8,8,W-2];counts=[0,2,1,0]
        elif index==9:
            source=12;targets=[26,4,22,6,25];counts=[2,0,4,1,0]
        else:
            count=rng.randint(1,4);source=rng.randint(W//2-2,W//2+2)
            high=rng.choice([True,False]);targets=[]
            for _ in range(count):
                targets.append(rng.randint(W-6,W-2) if high else rng.randint(1,5));high=not high
            counts=[rng.randint(0,4) for _ in targets]
        distances=[abs(b-a)+1 for a,b in zip([source]+targets,targets)]
        if distances.count(max(distances))!=1:continue
        walls=[];previous_row=0;previous_column=source
        for i,(target,n) in enumerate(zip(targets,counts)):
            d=n+1
            row=[5,9,15,21,29][i] if index==9 else previous_row+rng.randint(1,3)+d
            lo,hi=(0,target-d) if target>previous_column else (target+d,W-1)
            if not (0<=lo<=previous_column<=hi<W and row-d>previous_row):break
            walls.append((row,lo,hi,n));previous_row=row;previous_column=target
        if len(walls)!=len(targets):continue
        H=30 if index==9 else previous_row+rng.randint(2,6)
        if H>30:continue
        bg=rng.choice((0,4,5,6,7,8,9));g=[[bg]*W for _ in range(H)];g[0][source]=3
        for row,lo,hi,n in walls:
            marks=set(rng.sample(list(range(lo,hi+1)),n))
            for c in range(lo,hi+1):g[row][c]=1 if c in marks else 2
        if rng.choice((False,True)):g=[row[::-1] for row in g]
        g=rotate(g,rng.randrange(4))
        return g
    raise ValueError('Could not construct a unique-winner legal route after 100 bounded attempts')


def generate(seed, settings, demos, queries):
    scope=validate(settings)
    if type(seed) is not int:raise ValueError('integer seed required')
    if type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('demos=2..6; queries=1..4')
    bank=[];seen=set()
    for index in range(10):
        for attempt in range(50):
            g=scene(rng_for(seed,f'input-{index}-attempt-{attempt}'),index)
            identity=tuple(map(tuple,g))
            if identity not in seen:bank.append(g);seen.add(identity);break
        else:raise ValueError('Distinct input bank exhausted')
    order=list(range(6,10));rng_for(seed,'presentation').shuffle(order)
    pair=lambda g:dict(input=g,output=solve(g,scope))
    return {'train':[pair(g) for g in bank[:demos]],'test':[pair(bank[i]) for i in order[:queries]],
            'program_solution':program(settings),'settings':deepcopy(settings),
            'private':{'seed':seed,'query_source_indices':order[:queries]}}


def public_turn(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('Invalid query index')
    return deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                     'test':[{'input':episode['test'][index]['input']}]})


def rival_programs(settings):
    scope=validate(settings);p=program(settings)
    select=lambda name:p.replace("(define scope 'full)","(define scope 'longest)").replace("(define selector 'length)",f"(define selector '{name})")
    return {
        'opposite_scope':program({'trace_scope':'longest_bypass' if scope=='full_route' else 'full_route'}),
        'clearance_one':p.replace('(define fixed-clearance -1)','(define fixed-clearance 1)'),
        'clearance_two':p.replace('(define fixed-clearance -1)','(define fixed-clearance 2)'),
        'count_without_margin':p.replace('(define margin 1)','(define margin 0)'),
        'first_bypass':select('first'),'last_bypass':select('last'),
        'largest_marker_count':select('markers'),'widest_wall':select('width'),
        'start_relative_span':select('initial-span'),
    }


def rival_predict(g,scope,name):
    if name=='opposite_scope':return solve(g,'longest_bypass' if scope=='full_route' else 'full_route')
    return solve(g,scope,rival=name)


DEPENDENCY={
    'step_a':'Normalize the start edge, count each barrier’s blue markers, and trace the count-plus-one clearance waypoints in travel order.',
    'intermediate':'The ordered barriers with marker counts and the derived lateral segments: turn row, previous lane, new lane and actual length.',
    'step_b':'Select the unique longest lateral segment of that recovered route and render it while retaining the original source and red barriers.',
    'why_b_depends_on_a':'A segment starts on the lane chosen at the preceding barrier and ends beyond the current free tip by its count-derived clearance. Neither local marker count nor wall width determines its length.'}


def causal_case(episode):
    p=next(p for p in episode['test'] if len(p['input'])==len(p['input'][0])==30)
    f=inspect(p['input']);f={k:v for k,v in f.items() if k!='normalized'}
    return dict(input=p['input'],settings=episode['settings'],program=program(episode['settings']),output=p['output'],
                intermediate_value=f,counterfactual_program=rival_programs(episode['settings'])['clearance_two'],
                ablation='wrong_intermediate')
