"""Author-private constructive tile family. No official grids or gold are read here."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from functools import reduce
from math import gcd
from pathlib import Path
import hashlib
import random

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
OPTIONS=('ink','holes')

def rng_for(seed, tag):
    return random.Random(int.from_bytes(hashlib.sha256(f'a395ee82-v1|{seed}|{tag}'.encode()).digest(),'big'))

def components(g,bg):
    seen=set(); result=[]
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if v==bg or (r,c) in seen: continue
            todo=[(r,c)];seen.add((r,c));cells=[]
            while todo:
                x,y=todo.pop();cells.append((x,y))
                for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
                    p=(x+dx,y+dy)
                    if 0<=p[0]<len(g) and 0<=p[1]<len(g[0]) and p not in seen and g[p[0]][p[1]]==v:
                        seen.add(p);todo.append(p)
            result.append((v,sorted(cells)))
    return result

def inspect(g):
    bg=Counter(c for row in g for c in row).most_common(1)[0][0]
    obs=components(g,bg)
    if not obs: raise ValueError('No template')
    ink,cells=max(obs,key=lambda o:len(o[1]))
    anchors=[p[0] for v,p in obs if len(p)==1 and v==ink]
    marks=[(v,p[0]) for v,p in obs if len(p)==1 and v!=ink]
    if len(cells)<2 or len(anchors)!=1 or not marks: raise ValueError('Need one template and a separate anchored symbol map')
    if len({v for v,_ in marks})!=1: raise ValueError('Uniform remote symbol color required')
    r0=min(r for r,c in cells);c0=min(c for r,c in cells)
    sh=max(r for r,c in cells)-r0+1;sw=max(c for r,c in cells)-c0+1
    anchor=anchors[0]; points=[anchor]+[p for _,p in marks]
    def pitch(k):
        values=sorted({p[k] for p in points})
        return reduce(gcd,(v-values[0] for v in values[1:]),0) or 1
    return dict(bg=bg, ink=ink,tint=marks[0][0],cells=cells,anchor=anchor,
                origin=(r0,c0),shape=(sh,sw),pitch=(pitch(0),pitch(1)),marks=[p for _,p in marks])

def solve(g,mask='ink',*,rival=None):
    if mask not in OPTIONS: raise ValueError('Unknown mask')
    try: f=inspect(g)
    except ValueError: return deepcopy(g)
    H,W=len(g),len(g[0]);sh,sw=f['shape'];rr,cc=f['origin'];pr,pc=f['pitch'];ar,ac=f['anchor']
    if rival=='pitch_one': pr=pc=1
    if rival=='pitch_two': pr=pc=2
    if rival=='unit_stride': sh=sw=1
    out=deepcopy(g) if rival=='keep_map' else [[f['bg']]*W for _ in range(H)]
    for r,c in f['cells']: out[r][c]=f['ink'] if rival=='no_swap' else f['tint']
    mh,mw=f['shape']
    cells={(r-rr,c-cc) for r,c in f['cells']}
    selected=[(r,c) for r in range(mh) for c in range(mw) if rival=='solid_box' or ((r,c) in cells)==(mask=='ink')]
    for mr,mc in f['marks']:
        quot=lambda x,y: x//y if x>=0 else -((-x)//y)  # DSL division truncates toward zero.
        dr,dc=quot(mr-ar,pr),quot(mc-ac,pc)
        if rival=='transpose_map': dr,dc=dc,dr
        tr,tc=rr+sh*dr,cc+sw*dc
        for r,c in selected:
            x,y=tr+r,tc+c
            if 0<=x<H and 0<=y<W:out[x][y]=f['ink']
    return out

def validate(settings):
    if type(settings) is not dict or set(settings)!={'tile_mask'} or settings['tile_mask'] not in OPTIONS:
        raise ValueError('settings must be exactly tile_mask=ink|holes')
    return settings['tile_mask']

def program(settings):
    mask=validate(settings)
    return (BASE/'canonical.rkt' if mask=='ink' else BASE/'holes.rkt').read_text()

def shape_mask(rng,h,w):
    # Remove cells only when connectivity and the full bounding box survive.
    cells={(r,c) for r in range(h) for c in range(w)}
    order=sorted(cells);rng.shuffle(order)
    wanted=rng.randint(1,max(1,h*w//3))
    for p in order:
        trial=cells-{p}
        if min(x for x,y in trial)!=0 or max(x for x,y in trial)!=h-1 or min(y for x,y in trial)!=0 or max(y for x,y in trial)!=w-1:continue
        todo=[next(iter(trial))];seen=set(todo)
        while todo:
            x,y=todo.pop()
            for d in ((-1,0),(1,0),(0,-1),(0,1)):
                z=(x+d[0],y+d[1])
                if z in trial and z not in seen: seen.add(z);todo.append(z)
        if seen==trial: cells=trial;wanted-=1
        if wanted==0:break
    return sorted(cells)

def scene(rng,index):
    stress=index==9
    bg,ink,tint=rng.sample(range(10),3)
    if stress:
        H=W=30;h=w=5;rr=cc=15;pr=pc=4;ar,ac=12,14
        offsets=[(0,0),(-3,-3),(-3,2),(2,-3),(2,2),(-2,1),(-1,0),(1,-2),(1,0),(2,1)]
    else:
        H=rng.randint(22,29);W=rng.randint(22,29)
        h,w=[(3,4),(4,3),(2,4),(4,2),(3,3),(4,4),(2,3),(3,2),(4,4)][index%9]
        rr=rng.randint(h,H-2*h);cc=rng.randint(w,W-2*w)
        offsets=[(0,0),(-1,-1),(-1,1),(0,1),(1,-1)]
        extra=[(1,0),(1,1),(-1,0),(0,-1)];rng.shuffle(extra);offsets+=extra[:index%4]
        pr=4 if index==0 else rng.choice((2,3,4));pc=2 if index==0 else rng.choice((2,3,4))
        origins=[(a,b) for a in range(pr,H-pr) for b in range(pc,W-pc)
                 if all(not (rr-1<=a+dr*pr<=rr+h and cc-1<=b+dc*pc<=cc+w) for dr,dc in offsets)]
        if not origins: raise ValueError('No legal separated controller placement')
        ar,ac=rng.choice(origins)
    cells=shape_mask(rng,h,w)
    g=[[bg]*W for _ in range(H)]
    for r,c in cells:g[rr+r][cc+c]=ink
    for dr,dc in offsets:
        r,c=ar+dr*pr,ac+dc*pc
        if g[r][c]!=bg: raise ValueError('Controller overlaps template')
        g[r][c]=ink if (dr,dc)==(0,0) else tint
    f=inspect(g)
    if f['shape']!=(h,w) or f['pitch']!=(pr,pc):raise AssertionError('Construction decode mismatch')
    return g

def generate(seed,settings,demos,queries):
    mask=validate(settings)
    if type(seed) is not int:raise ValueError('integer seed required')
    if type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('demos=2..6; queries=1..4')
    bank=[scene(rng_for(seed,f'input-{i}'),i) for i in range(10)]
    order=list(range(6,10));rng_for(seed,'presentation').shuffle(order)
    pair=lambda g:dict(input=g,output=solve(g,mask))
    return {'train':[pair(g) for g in bank[:demos]],'test':[pair(bank[i]) for i in order[:queries]],
            'program_solution':program(settings),'settings':deepcopy(settings),
            'private':{'seed':seed,'query_source_indices':order[:queries]}}

def public_turn(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('Invalid query index')
    return deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                     'test':[{'input':episode['test'][index]['input']}]})

def rival_programs(settings):
    mask=validate(settings); p=program(settings)
    return {
        'opposite_mask':program({'tile_mask':'holes' if mask=='ink' else 'ink'}),
        'pitch_one':p.replace('(define pr (pitch obj-r1))','(define pr 1)').replace('(define pc (pitch obj-c1))','(define pc 1)'),
        'pitch_two':p.replace('(define pr (pitch obj-r1))','(define pr 2)').replace('(define pc (pitch obj-c1))','(define pc 2)'),
        'unit_stride':p.replace('(* sh (/','(* 1 (/').replace('(* sw (/','(* 1 (/'),
        'solid_box':p.replace('#:when (if holes? (= (at g (+ rr r) (+ cc c)) bg)\n                             (= (at g (+ rr r) (+ cc c)) ink))', '#:when #t'),
        'keep_map':p.replace('(empty-grid (rows g) (cols g) bg)','g'),
        'no_swap':p.replace('(obj-cells shape) tint)','(obj-cells shape) ink)'),
        'transpose_map':p.replace('(/ (- (obj-r1 mark) (obj-r1 anchor)) pr)', '(/ (- (obj-c1 mark) (obj-c1 anchor)) pc)').replace('(* sw (/ (- (obj-c1 mark) (obj-c1 anchor)) pc))','(* sw (/ (- (obj-r1 mark) (obj-r1 anchor)) pr))'),
    }

def rival_predict(g,mask,name):
    return solve(g,('holes' if mask=='ink' else 'ink') if name=='opposite_mask' else mask,
                 rival=None if name=='opposite_mask' else name)

DEPENDENCY={
 'step_a':'Discover the template and decode row and column pitches of the anchored sparse symbol map.',
 'intermediate':'Template bounding-box dimensions, ink/hole mask, map anchor and pitch-normalized tile offsets.',
 'step_b':'Scale the decoded offsets by template height and width, then stamp the selected mask at those destinations.',
 'why_b_depends_on_a':'The same marker displacement denotes a different number of tiles when the inferred map pitch changes; target placement also depends on the recovered template dimensions.'}

def causal_case(episode):
    pair=next(p for p in episode['test'] if len(p['input'])==len(p['input'][0])==30)
    settings=episode['settings'];f=inspect(pair['input'])
    return dict(input=pair['input'],settings=settings,program=program(settings),output=pair['output'],
                intermediate_value=f,counterfactual_program=rival_programs(settings)['pitch_one'],
                ablation='wrong_intermediate')
