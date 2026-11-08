"""Native matched-input rigid-block routing family; no original grids are sampled."""
from __future__ import annotations
from pathlib import Path
import copy
import hashlib
import importlib.util
import random
import sys
from puzzle_generators.base import gen_ctx

BASE=Path(__file__).resolve().parent
TASK='public_eval_332f06d7'
VERSION='1.0.1'

def local(name):
    path=BASE/(name+'.py');key='_motion_'+name+'_'+hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path)
        module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return sys.modules[key]

model=local('model')

def setting(settings):
    if type(settings) is not dict or set(settings)!={'travel'} or settings['travel'] not in ('terminal','halfway'):
        raise ValueError('settings must be exactly travel=terminal|halfway')
    return settings['travel']

def program(settings):
    return (BASE/('canonical.rkt' if setting(settings)=='terminal' else 'halfway.rkt')).read_text()

def rotate(grid,n,mirror=False):
    if mirror:grid=[row[::-1] for row in grid]
    for _ in range(n):grid=[list(row) for row in zip(*grid[::-1])]
    return grid

def _scene(seed,index):
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=TASK)
    rng=ctx.draw_rng('corridor');stress=index==103
    k={0:3,1:4,100:1,101:2,102:3,103:4}.get(index,rng.randrange(1,5))
    h=30 if stress else rng.randrange(24,31);w=30 if stress else rng.randrange(24,31)
    wall=rng.randrange(3,10)
    grid=[[wall]*w for _ in range(h)]
    lanes=5 if stress or index==101 else 3 if index in (0,1) else rng.randrange(3, min(5,(h+2)//(k+2))+1)
    top=0 if stress else rng.randrange(0,2)
    bottom=h-k if stress else h-k-rng.randrange(0,2)
    # Space lane anchors evenly, leaving at least two wall rows between bands.
    ys=[top+(bottom-top)*j//(lanes-1)for j in range(lanes)]
    left=0 if stress else rng.randrange(0,2);right=w-k if stress else w-k-rng.randrange(0,2)
    def block(r,c,color):
        for a in range(k):
            for b in range(k):grid[r+a][c+b]=color
    anchors=[]
    for j,y in enumerate(ys):
        xs=range(left,right+1) if j%2==0 else range(right,left-1,-1)
        for x in xs:anchors.append((y,x));block(y,x,1)
        if j+1<lanes:
            x=right if j%2==0 else left
            for yy in range(y+1,ys[j+1]+1):anchors.append((yy,x));block(yy,x,1)
    blocked=k>1 and (index in (1,101,103) or index not in (0,100,102) and index%2==1)
    cut_lane=3 if stress else 1
    if blocked:
        # Preserve a point-wide route but deny the full rigid footprint.
        cut_left=(left+right)//2-rng.randrange(0,2);cut_width=rng.randrange(2,5)
        for c in range(cut_left,cut_left+cut_width):grid[ys[cut_lane]][c]=wall
    for j,y in enumerate(ys[:-1]):
        if blocked and j==cut_lane:continue
        # One-sided alcoves preserve a separating wall row, introduce legal
        # anchor branches and avoid reducing every scene to a single thin line.
        x=rng.randrange(left+2,max(left+3,right-k-1))
        for c in range(x,min(x+k+2,right)):
            if y+k<ys[j+1]-1:grid[y+k][c]=1
    start=(ys[0],left)
    # Sometimes the red destination precedes a blue dead-end extension. This
    # distinguishes the goal-directed rule from simply maximizing travel.
    goal_back=6 if index==0 else 0 if blocked else rng.randrange(0,5)
    if index==0 and (lanes*(right-left)+ys[-1]-ys[0]-goal_back)%2==0:
        goal_back+=1  # An odd legal route teaches ceil rather than floor halfway.
    goal=(ys[-1],right-goal_back if (lanes-1)%2==0 else left+goal_back)
    block(*start,0);block(*goal,2)
    grid=rotate(grid,rng.randrange(4),rng.choice((False,True)))
    data=model.analyze(grid)
    if len(data['route'])<3:raise RuntimeError('nontrivial movement required')
    if (data['scores'][data['terminal']]>0)!=blocked:raise RuntimeError('bottleneck construction did not match intended clearance')
    return grid


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
