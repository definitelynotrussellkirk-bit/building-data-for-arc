"""Native matched-input two-stage voting family; no original grids are sampled."""
from __future__ import annotations
from pathlib import Path
import copy
import hashlib
import importlib.util
import random
import sys
from puzzle_generators.base import gen_ctx

BASE=Path(__file__).resolve().parent
TASK='public_eval_800d221b'
VERSION='1.0.1'

def local(name):
    path=BASE/(name+'.py');key='_network_'+name+'_'+hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path)
        module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return sys.modules[key]

model=local('model')

def setting(settings):
    if type(settings) is not dict or set(settings)!={'aggregation'} or settings['aggregation'] not in ('contacts','chambers'):
        raise ValueError('settings must be exactly aggregation=contacts|chambers')
    return settings['aggregation']

def program(settings):
    return (BASE/('canonical.rkt' if setting(settings)=='contacts' else 'chambers.rkt')).read_text()

def rotate(grid,n,mirror=False):
    if mirror:grid=[row[::-1] for row in grid]
    for _ in range(n):grid=[list(row) for row in zip(*grid[::-1])]
    return grid

def _scene(seed,index):
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=TASK)
    rng=ctx.draw_rng('geometry');stress=index==103
    h=30 if stress else rng.randrange(24,31);w=30 if stress else rng.randrange(24,31)
    hr,hc=h//2,w//2
    bg,wire,a,b=rng.sample(range(10),4)
    a,b=sorted((a,b),reverse=bool(index%2))
    g=[[bg]*w for _ in range(h)]
    def segment(p,q):
        r,c=p;rr,cc=q
        if r!=rr and c!=cc:raise ValueError('axis-aligned segment required')
        for x in range(min(r,rr),max(r,rr)+1):
            for y in range(min(c,cc),max(c,cc)+1):g[x][y]=wire
    def route(*points):
        for p,q in zip(points,points[1:]):segment(p,q)
    def chamber(rect,winner):
        top,left,bottom,right=rect
        for r in range(top,bottom+1):
            for c in range(left,right+1):
                if r in (top,bottom) or c in (left,right):g[r][c]=wire
        positions=[(r,c) for r in range(top+1,bottom) for c in range(left+1,right)]
        n=len(positions);wanted_global=b if index%2==0 else a
        count=n-1 if winner==wanted_global else n//2+1
        values=[winner]*count+[a if winner==b else b]*(n-count);rng.shuffle(values)
        for (r,c),value in zip(positions,values):g[r][c]=value
    # Three terminals with contact weights 3:1:1, or five with 2:1:1:2:1.
    # The contact winner is A and the chamber winner B in every geometry.
    five=stress or index%3!=0
    if five:
        tl=(0,0,6 if stress else rng.randrange(4,7),6 if stress else rng.randrange(4,7))
        bl=(h-(8 if stress else rng.randrange(6,9)),0,h-1,6 if stress else rng.randrange(4,7))
        tr=(0,hc+1,5 if stress else rng.randrange(3,6),hc+(8 if stress else rng.randrange(6,9)))
        mr=(hr-4,w-(6 if stress else rng.randrange(4,7)),hr+3,w-1)
        br=(h-(7 if stress else rng.randrange(5,8)),hc+1,h-1,hc+(8 if stress else rng.randrange(6,9)))
        if index==1:
            # Complement the first demo's area and extremal-position shortcuts.
            tl=(0,0,6,6);bl=(h-8,0,h-1,6)
            tr=(0,hc+1,3,hc+6);mr=(hr-4,w-4,hr+3,w-1)
            br=(h-5,hc+1,h-1,hc+6)
        for rect,color in [(tl,a),(tr,b),(mr,b),(bl,a),(br,b)]:chamber(rect,color)
        route((hr-2,hc-1),(2,hc-1),(2,tl[3]))
        route((hr-1,hc-2),(hr-1,2),(tl[2],2))
        route((hr-2,hc+1),(tr[2],hc+1))
        route((hr-1,hc+2),(hr-1,mr[1]))
        route((hr+1,hc-2),(hr+1,2),(bl[0],2))
        route((hr+2,hc-1),(h-3,hc-1),(h-3,bl[3]))
        route((hr+2,hc+1),(br[0],hc+1))
    else:
        top=(0,hc-rng.randrange(3,5),rng.randrange(3,6),hc+rng.randrange(3,5))
        bl=(h-rng.randrange(5,8),0,h-1,rng.randrange(4,7))
        br=(h-rng.randrange(5,8),w-rng.randrange(5,8),h-1,w-1)
        if index==0:
            # The contact-winning terminal is the unique smallest chamber.
            top=(0,hc-3,3,hc+3);bl=(h-7,0,h-1,6);br=(h-8,w-7,h-1,w-1)
        for rect,color in [(top,a),(bl,b),(br,b)]:chamber(rect,color)
        route((hr-2,hc-1),(top[2],hc-1))
        route((hr-2,hc+1),(top[2],hc+1))
        route((hr-1,hc-2),(hr-1,2),(2,2),(2,top[1]))
        route((hr+2,hc-1),(h-3,hc-1),(h-3,bl[3]))
        route((hr+1,hc+2),(hr+1,w-3),(br[0],w-3))
    for r in range(hr-1,hr+2):
        for c in range(hc-1,hc+2):g[r][c]=wire
    if index in (0,1):
        prefix_ctx=gen_ctx(seed=seed,sample_index=0,version=VERSION,task_id=TASK)
        wanted=bool(prefix_ctx.draw_rng('prefix-orientation').randrange(2))
        if index==1:wanted=not wanted
        orientations=[(turn,flip) for turn in range(4) for flip in (False,True)]
        rng.shuffle(orientations)
        # Components are ordered by their earliest WIRE cell, not box position.
        for turn,flip in orientations:
            candidate=rotate(g,turn,flip);terms=model.analyze(candidate)['terminals']
            if (terms[0]['winner']==a)==wanted and (terms[-1]['winner']==a)!=wanted:
                g=candidate;break
        else:raise RuntimeError('No teaching-safe orientation')
    else:
        g=rotate(g,rng.randrange(4),rng.choice((False,True)))
    data=model.analyze(g)
    expected=5 if five else 3
    if len(data['terminals'])!=expected:raise RuntimeError('terminal construction merged or split')
    if model.solve(g,'contacts')==model.solve(g,'chambers'):raise RuntimeError('settings not distinguished')
    return g

def sample_input(seed,index):
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0:
        raise ValueError('seed and index must be nonnegative exact integers')
    return _scene(seed,index)

def generate(seed,settings,demos,queries):
    mode=setting(settings)
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('invalid seed')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    def pair(index):
        g=sample_input(seed,index);return {'input':g,'output':model.solve(g,mode)}
    train=[pair(i) for i in range(demos)];bank=[pair(100+i) for i in range(4)]
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'program_solution':program(settings),
            'settings':copy.deepcopy(settings),'seed':seed,'private':{'query_bank':bank}}

def public_view(episode,turn=0,presentation_seed=0):
    if type(turn) is not int or not 0<=turn<4:raise ValueError('turn must be 0..3')
    if type(presentation_seed) is not int:raise ValueError('presentation seed must be an integer')
    bank=episode['private']['query_bank']
    if len(bank)!=4:raise ValueError('exactly four private queries required')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    train=[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])} for p in episode['train']]
    return {'train':train,'test':[{'input':copy.deepcopy(bank[order[turn]]['input'])}]}
