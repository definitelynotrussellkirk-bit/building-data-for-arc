"""Native legend-controlled movement, including no-corner-cutting stress."""
from __future__ import annotations
from pathlib import Path
import copy
import hashlib
import importlib.util
import random
import sys
from puzzle_generators.base import gen_ctx

BASE=Path(__file__).resolve().parent
TASK='public_eval_88e364bc'
VERSION='1.0.0'

def local(name):
    path=BASE/(name+'.py');key='_88e_'+name+'_'+hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path)
        module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return sys.modules[key]

model=local('model')


def setting(settings):
    if type(settings) is not dict or set(settings)!={'motion_extent'} or settings['motion_extent'] not in ('to_wall','halfway'):
        raise ValueError('settings must name exactly motion_extent=to_wall|halfway')
    return settings['motion_extent']


def program(settings):
    mode=setting(settings)
    return (BASE/('canonical.rkt' if mode=='to_wall' else 'halfway.rkt')).read_text()


def rotate_grid(grid,n):
    for _ in range(n):grid=[list(row) for row in zip(*grid[::-1])]
    return grid


def _legend(color,body,direction):
    tile=[[color]*7 for _ in range(7)]
    dr,dc=direction
    if dr and dc:
        starts=[(1,3),(2,1)];base=(1,1)
    else:
        starts=[(2,1),(4,1)];base=(0,1)
    for r,c in starts:
        for k in range(3):tile[r+k*base[0]][c+k*base[1]]=2 if k==2 else body
    d=base
    for turns in range(4):
        if d==direction:return rotate_grid(tile,turns)
        d=(d[1],-d[0])
    raise ValueError('Unsupported legend direction')


def raw_run(g,p,d):
    r,c=p;dr,dc=d;count=0
    while 0<=r+dr<len(g) and 0<=c+dc<len(g[0]) and g[r+dr][c+dc] in (0,4):
        r+=dr;c+=dc;count+=1
    return count


def _scene(seed,index):
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=TASK)
    stress=index==103
    for attempt in range(80):
        rng=ctx.draw_rng(f'layout-{attempt}')
        rooms=3 if index in (102,103) else 2
        n=2 if index==102 else rooms
        h=30 if stress else rng.randrange(24,31)
        w=30 if stress else rng.randrange(27 if rooms==3 else 23,31)
        g=[[0]*w for _ in range(h)]
        colors=rng.sample([1,3,5,6,7,8,9],n)
        if index%3==0:dirs=[(1,1),(-1,-1),(0,1)][:n]
        elif index%3==1:dirs=[(0,1),(1,0),(-1,-1)][:n]
        else:dirs=[(-1,-1),(0,-1),(1,1)][:n]
        palette={color:direction for color,direction in zip(colors,dirs)}
        legend_order=list(colors);rng.shuffle(legend_order)
        for j,color in enumerate(legend_order):
            body=rng.choice([v for v in range(1,10) if v not in (2,4,color)])
            tile=_legend(color,body,palette[color]);left=(w-(8*n-1))//2+8*j
            for r in range(7):
                for c in range(7):g[r][left+c]=tile[r][c]
        roomcolors=colors+[colors[0]] if rooms>n else colors.copy()
        rng.shuffle(roomcolors)
        selected=[];corner_count=0;valid=True
        for j,color in enumerate(roomcolors):
            left=j*w//rooms;right=(j+1)*w//rooms-2 if j<rooms-1 else w-1
            top=9;bottom=h-1;mid=left+(right-left)//2
            for r in range(top,bottom+1):
                for c in range(left,right+1):
                    if r in (top,bottom) or c in (left,right):g[r][c]=color
            # Connected teeth create nonconvex rooms and diagonal wall corners.
            tooth_end=top+rng.randrange(3,6)
            for r in range(top,tooth_end+1):g[r][mid]=color
            notch=top+(bottom-top)//2
            for c in range(left,left+3):g[notch][c]=color
            for c in range(right-2,right+1):g[bottom-3][c]=color
            d=palette[color]
            available=[]
            for r in range(top+1,bottom):
                for c in range(left+1,right):
                    if g[r][c]:continue
                    distance=model.free_run(g,(r,c),d)
                    raw=raw_run(g,(r,c),d)
                    if distance>=2:
                        available.append(((r,c),distance,raw))
            rng.shuffle(available)
            corners=[a for a in available if a[2]>=a[1]+2]
            long=[a for a in available if a[1]>=3]
            if not long:valid=False;break
            picks=[];ends=set();halfends=set()
            # First put a demonstrable no-corner-cutting case when available.
            ordered=(corners[:1]+long+available)
            for p,dist,raw in ordered:
                end=(p[0]+dist*d[0],p[1]+dist*d[1])
                hd=(dist+1)//2;half=(p[0]+hd*d[0],p[1]+hd*d[1])
                if end in ends or half in halfends or p in [x[0] for x in picks]:continue
                picks.append((p,dist,raw));ends.add(end);halfends.add(half)
                if len(picks)==(4 if stress else 3):break
            if len(picks)<2:valid=False;break
            for p,dist,raw in picks:
                g[p[0]][p[1]]=4;selected.append(p)
                corner_count+=raw>=dist+2
        if not valid or (index%3==0 and not corner_count):continue
        g=rotate_grid(g,rng.randrange(4))
        data=model.analyze(g)
        if len(data['legends'])!=n or len(data['particles'])!=len(selected):continue
        if len({p['direction'] for p in data['particles']})<2:continue
        if model.solve(g)==model.solve(g,'halfway'):continue
        return g
    raise RuntimeError(f'Bounded scene construction failed: seed={seed}, index={index}')


def sample_input(seed,index):
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0:
        raise ValueError('seed and sample index must be nonnegative exact integers')
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
    if type(presentation_seed) is not int:raise ValueError('presentation_seed must be an integer')
    bank=episode['private']['query_bank']
    if len(bank)!=4:raise ValueError('exactly four private queries required')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    train=[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])} for p in episode['train']]
    return {'train':train,'test':[{'input':copy.deepcopy(bank[order[turn]]['input'])}]}
