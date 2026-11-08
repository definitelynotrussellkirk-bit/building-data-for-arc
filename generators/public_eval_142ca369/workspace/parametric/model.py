"""Constructive reflected-ray family; no official inputs/answers imported."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from pathlib import Path
import hashlib
import random
BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
OPTIONS=('all_legs','longest_leg')

def rng_for(seed,tag):
    return random.Random(int.from_bytes(hashlib.sha256(f'142ca369-v1|{seed}|{tag}'.encode()).digest(),'big'))

def components(g):
    seen=set();obs=[]
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if not v or (r,c) in seen:continue
            todo=[(r,c)];seen.add((r,c));cells=[]
            while todo:
                x,y=todo.pop();cells.append((x,y))
                for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
                    p=(x+dx,y+dy)
                    if 0<=p[0]<len(g) and 0<=p[1]<len(g[0]) and p not in seen and g[p[0]][p[1]]==v:
                        seen.add(p);todo.append(p)
            obs.append((v,sorted(cells)))
    return obs

def trace(g,*,rival=None):
    sources=[];mirrors=[]
    for color,cells in components(g):
        rs=[r for r,c in cells];cs=[c for r,c in cells]
        h=max(rs)-min(rs)+1;w=max(cs)-min(cs)+1
        if len(cells)==3 and (h,w)==(2,2):
            elbow=next(p for p in cells if sum(abs(p[0]-q[0])+abs(p[1]-q[1])==1 for q in cells)==2)
            dr=-1 if elbow[0]==min(rs) else 1;dc=-1 if elbow[1]==min(cs) else 1
            sources.append((elbow,dr,dc,color))
        elif len(cells)==1 or (len(cells)==3 and (h==1 or w==1)):
            mirrors.append(((min(rs)+max(rs))//2,(min(cs)+max(cs))//2,2 if len(cells)==1 else 0 if h==1 else 1,color))
    if rival=='no_reflection':mirrors=[]
    paths=[]
    for elbow,dr,dc,color in sources:
        r,c=elbow[0]+dr,elbow[1]+dc;seen=set();leg=0;path=[];bounces=[]
        while 0<=r<len(g) and 0<=c<len(g[0]) and not g[r][c] and (r,c,dr,dc) not in seen:
            seen.add((r,c,dr,dc));incoming=color
            hm=next((m for m in mirrors if m[0]==r+dr and m[1]==c and m[2]!=1),None)
            vm=next((m for m in mirrors if m[0]==r and m[1]==c+dc and m[2]!=0),None)
            hit=hm or vm
            if hit:
                if rival!='no_reflection_turn':
                    if hm:dr=-dr
                    else:dc=-dc
                if rival!='source_color':color=hit[3]
                leg+=1;bounces.append({'position':[r,c],'mirror':list(hit),'outgoing':[dr,dc],'color':color})
            path.append((r,c,incoming if rival=='late_color' and hit else color,leg))
            r+=dr;c+=dc
        sizes=Counter(p[3] for p in path)
        paths.append({'source':list(elbow),'cells':path,'bounces':bounces,'lengths':dict(sizes),
                      'winner':max(sizes,key=sizes.get) if sizes else None})
    return paths

def solve(g,scope='all_legs',*,rival=None):
    if scope not in OPTIONS:raise ValueError('Unknown trace scope')
    out=deepcopy(g)
    for ray in trace(g,rival=rival):
        lengths=ray['lengths'];chosen=ray['winner']
        if lengths and rival=='first_leg':chosen=min(lengths)
        if lengths and rival=='last_leg':chosen=max(lengths)
        if lengths and rival=='shortest_leg':chosen=min(lengths,key=lengths.get)
        chosen_color=next((p[2] for p in ray['cells'] if p[3]==chosen),None)
        if rival=='total_color' and ray['cells']:
            totals=Counter(p[2] for p in ray['cells']);chosen_color=max(totals,key=totals.get)
        for r,c,color,leg in ray['cells']:
            keep=color==chosen_color if rival in ('total_color','winning_color') else leg==chosen
            if scope=='all_legs' or keep:out[r][c]=color
    return out

def validate(settings):
    if type(settings) is not dict or set(settings)!={'trace_scope'} or settings['trace_scope'] not in OPTIONS:
        raise ValueError('settings must be exactly trace_scope=all_legs|longest_leg')
    return settings['trace_scope']

def program(settings):
    scope=validate(settings)
    return (HOME/'reference.rkt' if scope=='all_legs' else BASE/'longest.rkt').read_text()

def transform(g,index):
    if type(index) is not int or not 0<=index<8:raise ValueError('D4 index 0..7')
    out=deepcopy(g)
    if index>=4:out=[row[::-1] for row in out]
    for _ in range(index%4):out=[list(row) for row in zip(*out[::-1])]
    return out

def scene(rng,index):
    # A constructive zigzag with V,V,H,H reflections; small lawful parameter
    # changes preserve room for the whole route. Cases cover first/middle/last winners.
    kind=index%3
    if index==9:
        H=W=30;lengths=[8,6,13,10];shift_r=shift_c=0;extra=True
    elif index==7:
        H=24;W=24;lengths=[8];shift_r=shift_c=0;extra=True
    elif kind==0 and index!=6:
        d1=rng.choice((4,5));lengths=[d1,d1-1,rng.choice((4,5)),rng.choice((3,4))]
        H=22+rng.randrange(2);W=26+rng.randrange(2);shift_r=shift_c=0;extra=False
    elif kind==1:
        d1=rng.choice((5,6));d3=rng.choice((7,8));lengths=[d1,d1-1,d3,d3-1]
        H=23+rng.randrange(2);W=20+rng.randrange(2);shift_r=shift_c=0;extra=False
    else:
        lengths=[rng.choice((12,13)),rng.choice((3,4)),rng.choice((2,3)),2]
        H=26;W=22+rng.randrange(2);shift_r=shift_c=0;extra=False
    colors=rng.sample(range(1,10),len(lengths)+1+int(extra))
    if len(lengths)==4:
        if index%3!=1: colors[4]=colors[0]  # Winner color can recur on a short leg.
        if index%3!=0 or index==9: colors[3]=colors[1]  # Aggregate color is not leg length.
    g=[[0]*W for _ in range(H)]
    def put(cells,color):
        for r,c in cells:
            if not (0<=r<H and 0<=c<W) or g[r][c]:raise ValueError('Gadget overlap or off-grid')
        for r,c in cells:g[r][c]=color
    r=c=1
    put([(r-1,c),(r,c-1),(r,c)],colors[0]);dr=dc=1
    for j,distance in enumerate(lengths):
        r+=dr*distance;c+=dc*distance
        vertical=j<2
        mr,mc=(r,c+dc) if vertical else (r+dr,c)
        # Singles and bars both appear; their center/normal is what matters.
        singleton=(index+j)%3==0
        cells=[(mr,mc)] if singleton else ([(mr+u,mc) for u in (-1,0,1)] if vertical else [(mr,mc+u) for u in (-1,0,1)])
        put(cells,colors[j+1])
        if vertical:dc=-dc
        else:dr=-dr
    if extra:put([(0,W-2),(1,W-1),(1,W-2)],colors[-1])
    paths=trace(g)
    # Protect the grammar rather than silently accepting an unintended interaction.
    first=paths[0]
    if len(first['bounces'])!=len(lengths):raise AssertionError(('Unexpected reflection route',index,first))
    if len(first['lengths'])!=len(lengths)+1:raise AssertionError('Missing ray leg')
    if list(first['lengths'].values()).count(max(first['lengths'].values()))!=1:raise AssertionError(('Tied longest leg',index,first['lengths']))
    return transform(g,rng.randrange(8))

def generate(seed,settings,demos,queries):
    scope=validate(settings)
    if type(seed) is not int:raise ValueError('Integer seed required')
    if type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('demos=2..6; queries=1..4')
    bank=[scene(rng_for(seed,f'input-{i}'),i) for i in range(10)]
    order=list(range(6,10));rng_for(seed,'presentation').shuffle(order)
    pair=lambda g:dict(input=g,output=solve(g,scope))
    return {'train':[pair(g) for g in bank[:demos]],'test':[pair(bank[i]) for i in order[:queries]],
            'program_solution':program(settings),'settings':deepcopy(settings),
            'private':{'seed':seed,'query_source_indices':order[:queries]}}

def public_turn(e,index):
    if type(index) is not int or not 0<=index<len(e['test']):raise ValueError('Invalid query index')
    return deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in e['train']],
                     'test':[{'input':e['test'][index]['input']}]})

def rival_programs(settings):
    mode=validate(settings);p=program(settings)
    only=p.replace('(define longest? #f)','(define longest? #t)')
    selected=next(line for line in p.splitlines() if '(define selected ' in line)
    def selector(expr):
        return only.replace(selected, '    (define selected (if (null? legs) -1 '+expr+'))')
    aggregate=only.replace('(define legs (remove-duplicates (map (lambda (p) (list-ref p 3)) path)))',
                          '(define legs (remove-duplicates (map (lambda (p) (list-ref p 2)) path)))')
    aggregate=aggregate.replace(selected,selected.replace('(list-ref p 3)','(list-ref p 2)'))
    aggregate=aggregate.replace('(= (list-ref p 3) selected)','(= (list-ref p 2) selected)')
    repeated=only.replace(selected,selected+'\n    (define chosen-color (if (null? path) -1 (for/first ((p path) #:when (= (list-ref p 3) selected)) (list-ref p 2))))')
    # Change the rendering selector, not the chosen-color lookup itself.
    repeated=repeated.replace('#:when (or (not longest?) (= (list-ref p 3) selected))',
                              '#:when (or (not longest?) (= (list-ref p 2) chosen-color))')
    before,rest=p.split('   (define mirrors',1)
    _,after=rest.split('   (define (walk',1)
    return {
      'opposite_scope':program({'trace_scope':'longest_leg' if mode=='all_legs' else 'all_legs'}),
      'no_reflection':before+"   (define mirrors '())\n   (define (walk"+after,
      'source_color':p.replace('(define color (if hit (list-ref hit 3) tint))','(define color tint)'),
      'no_reflection_turn':p.replace('(define nd-r (if hm (- dr) dr))','(define nd-r dr)').replace('(define nd-c (if (and vm (not hm)) (- dc) dc))','(define nd-c dc)'),
      'late_color':p.replace('(cons (list r c color next-leg)','(cons (list r c tint next-leg)'),
      'first_leg':selector('(first legs)'),
      'last_leg':selector('(last legs)'),
      'shortest_leg':selector('(pick-min legs (lambda (k) (count-if (lambda (p) (= (list-ref p 3) k)) path)))'),
      'total_color':aggregate,
      'winning_color':repeated,
    }

def rival_predict(g,mode,name):
    if name=='opposite_scope':return solve(g,'longest_leg' if mode=='all_legs' else 'all_legs')
    if name in ('first_leg','last_leg','shortest_leg','total_color','winning_color'):
        return solve(g,'longest_leg',rival=name)
    return solve(g,mode,rival=name)

DEPENDENCY={
 'step_a':'Trace each diagonal source through the original reflectors, recording color changes and segment boundaries at every bounce.',
 'intermediate':'For each source, the recovered ordered ray legs, their cell counts and the earliest maximum-length leg identifier.',
 'step_b':'Retain only the cells belonging to that selected longest leg, preserving all original gadget pixels.',
 'why_b_depends_on_a':'The winning leg and its color cannot be known from a source or single mirror: the complete input-dependent reflection route determines its boundaries and length. Repeated colors make total color area an incorrect substitute.'}

def causal_case(episode):
    pair=next(p for p in episode['test'] if len(p['input'])==len(p['input'][0])==30)
    facts=[{k:v for k,v in ray.items() if k!='cells'} for ray in trace(pair['input'])]
    return dict(input=pair['input'],settings=episode['settings'],program=program(episode['settings']),output=pair['output'],
                intermediate_value=facts,counterfactual_program=rival_programs(episode['settings'])['first_leg'],
                ablation='wrong_intermediate')
