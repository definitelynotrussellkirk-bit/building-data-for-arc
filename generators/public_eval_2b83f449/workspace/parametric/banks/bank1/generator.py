"""2b83f449: bridge-defined cyan paths and conserved green tokens.

Authoring gold is never imported by transformation or sampling code.
"""
from __future__ import annotations
import hashlib
import random

GENERATOR_ID=TASK_ID='public_eval_2b83f449'
VERSION='1.0.0'
SUMMARY='Install orange bridges as cyan paths with magenta dividers; route green tokens to their lower endpoints.'
EXAMPLES_NEEDED=2
MIN_STRICT_FRAC=1.0
AXES={}
INVARIANTS=['complete cyan strips alternate with black bridge rows', 'orange bridges are length-three horizontal bars',
 'green tokens start at side endpoints', 'installed cyan regions are paths or token-free cycles']


def check_grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v)is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected a rectangular 1..30 grid of integer colors 0..9')


def bridges(g):
    return [(r,c)for r in range(1,len(g)-1)for c in range(1,len(g[0])-1)if g[r][c-1:c+2]==[7,7,7]]


def install(g,base=None,variant='normal'):
    out=[row[:]for row in base] if base is not None else [[8 if v==3 else v for v in row]for row in g]
    for r,c in bridges(g):
        out[r][c-1:c+2]=[8,6,8]
        if variant!='center_only':out[r-1][c]=out[r+1][c]=6
    if variant=='ignore_holes':
        for r in range(0,len(g),2):
            for c in range(len(g[0])):
                if out[r][c]==0:out[r][c]=8
    if variant=='no_dividers':out=[[8 if v==6 else v for v in row]for row in out]
    return out


def components(net,connectivity=4):
    seen=set();result=[]
    steps=((-1,0),(1,0),(0,-1),(0,1))+(((-1,-1),(-1,1),(1,-1),(1,1))if connectivity==8 else ())
    for r,row in enumerate(net):
        for c,v in enumerate(row):
            if v!=8 or (r,c)in seen:continue
            todo=[(r,c)];seen.add((r,c));group=[]
            while todo:
                p=todo.pop();group.append(p)
                for dr,dc in steps:
                    q=p[0]+dr,p[1]+dc
                    if 0<=q[0]<len(net) and 0<=q[1]<len(row) and net[q[0]][q[1]]==8 and q not in seen:seen.add(q);todo.append(q)
            result.append(sorted(group))
    return result


def neighbors(p,region):
    return sorted(q for q in ((p[0]+1,p[1]),(p[0]-1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1))if q in region)


def pack(net,source,direction='down',policy='endpoint'):
    out=[row[:]for row in net]
    for cells in components(net):
        region=set(cells);tokens=[p for p in cells if source[p[0]][p[1]]==3]
        if not tokens:continue
        ends=[p for p in cells if len(neighbors(p,region))<=1]
        if policy=='original_side':
            row=max(r for r,c in cells)if direction=='down'else min(r for r,c in cells)
            cols=sorted(c for r,c in cells if r==row)
            nl=sum(c==0 for r,c in tokens);nr=len(tokens)-nl
            selected=[(row,c)for c in cols[:nl]+(cols[-nr:]if nr else [])]
        else:
            if not ends:selected=tokens
            else:
                if policy=='left_endpoint':options=[min(ends,key=lambda p:(p[1],p[0]))]
                elif policy=='right_endpoint':options=[max(ends,key=lambda p:(p[1],p[0]))]
                else:
                    level=(max if direction=='down'else min)(r for r,c in ends)
                    options=[p for p in ends if p[0]==level]
                if len(options)!=1:selected=tokens
                else:
                    selected=[];current=options[0];previous=None
                    for _ in range(len(tokens)):
                        selected.append(current)
                        nxt=[p for p in neighbors(current,region)if p!=previous]
                        if not nxt:break
                        previous,current=current,nxt[0]
        for r,c in selected:out[r][c]=3
    return out


def solve(g,mode='down'):
    check_grid(g)
    if mode not in ('down','up'):raise ValueError('unknown mode')
    return pack(install(g),g,mode)


def wrong_order(g,mode='down'):
    before=[[8 if v==3 else 0 if v==7 else v for v in row]for row in g]
    return install(g,pack(before,g,mode))


def policy_outputs(g):
    net=install(g)
    out={'identity':[row[:]for row in g], 'bridges_only':net}
    for mode in ('down','up'):
        out[mode]=pack(net,g,mode)
        out[mode+'_before_bridges']=wrong_order(g,mode)
        for policy in ('original_side','left_endpoint','right_endpoint'):
            out[mode+'_'+policy]=pack(net,g,mode,policy)
        for variant in ('ignore_holes','no_dividers','center_only'):
            out[mode+'_'+variant]=pack(install(g,variant=variant),g,mode)
    return out


def self_check(g,*,difficulty=None,meta=None):
    try:check_grid(g)
    except ValueError as e:return [str(e)]
    h,w=len(g),len(g[0]);errors=[]
    if h%2!=1 or h<3 or w<7:return ['complete alternating strips require odd height >=3 and width >=7']
    if any(v not in (0,3,7,8)for row in g for v in row):errors.append('unsupported input color')
    # Reject overlapping windows of longer orange runs, rather than treating them
    # as multiple bridges. The source grammar has separated bars of exactly three.
    for r in range(1,h,2):
        c=0
        while c<w:
            if g[r][c]!=7:c+=1;continue
            start=c
            while c<w and g[r][c]==7:c+=1
            if c-start!=3 or start<1 or c>w-1:errors.append('bridges must be separated length-three bars with side margins')
    centers=bridges(g)
    covered={(r,c+d)for r,c in centers for d in (-1,0,1)}
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if r%2==0:
                if v not in (0,3,8)or(v==3 and c not in (0,w-1)):errors.append('invalid cyan-strip cell')
            elif v not in (0,7)or(v==7 and (r,c)not in covered):errors.append('invalid bridge-row cell')
    if not centers:errors.append('at least one bridge required')
    net=install(g)
    for group in components(net):
        region=set(group)
        if any(len(neighbors(p,region))>2 for p in group):errors.append('branching installed track')
        if any(g[r][c]==3 for r,c in group)and not any(len(neighbors(p,region))<=1 for p in group):errors.append('token in a closed cycle')
    if sum(row.count(3)for row in net)!=0:errors.append('unconverted token')
    return sorted(set(errors))


def sample(seed,index,*,size=None):
    rng=random.Random(int.from_bytes(hashlib.sha256(f'{TASK_ID}:{seed}:{index}'.encode()).digest(),'big'))
    for attempt in range(64):
        h,w=size or (rng.choice(range(9,24,2)),rng.randint(12,27))
        g=[[0]*w for _ in range(h)]
        for r in range(0,h,2):
            g[r]=[8]*w
            if r<h-1:
                for c in (0,w-1):
                    if rng.random()<0.9:g[r][c]=3
        previous=[];layers=[]
        for r in range(1,h-1,2):
            options=list(range(2,w-2));rng.shuffle(options);cs=[]
            wanted=rng.randrange(0,1+min(3,(w-3)//4))
            for c in options:
                if len(cs)>=wanted:break
                if c not in previous and all(abs(c-x)>=4 for x in cs):cs.append(c)
            for c in cs:g[r][c-1:c+2]=[7,7,7]
            layers.append((r,cs));previous=cs
        for r in range(0,h,2):
            forbidden={c+d for rr,cs in layers if abs(rr-r)==1 for c in cs for d in (-1,0,1)}
            choices=[c for c in range(1,w-1)if c not in forbidden]
            rng.shuffle(choices)
            # Holes include interior endpoints, crucial to defeat boundary-side routing.
            for c in choices[:rng.randint(0,min(2,len(choices)))]:
                if rng.random()<0.65:g[r][c]=0
        if self_check(g):continue
        if solve(g)==install(g)or solve(g)==solve(g,'up'):continue
        return g
    raise RuntimeError('bounded path sampler exhausted 64 attempts')


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed)is not int or not 0<=seed<2**63 or type(sample_index)is not int or sample_index<0:raise ValueError('nonnegative integer seed/index required')
    if difficulty not in (None,'easy','medium','hard')or overrides:raise ValueError('unsupported controls')
    return sample(seed,sample_index,size={'easy':(9,12),'medium':(17,22),'hard':(29,30)}.get(difficulty))
