"""Matched-input marker-directed composition; self-contained native resources."""
from __future__ import annotations
from pathlib import Path
import copy
import hashlib
import importlib.util
import random
import sys
from puzzle_generators.base import gen_ctx
BASE=Path(__file__).resolve().parent
TASK='public_eval_7491f3cf'
VERSION='1.0.1'


def local(name):
    path=BASE/(name+'.py');key='_partition_'+name+'_'+hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path)
        module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return sys.modules[key]

model=local('model')


def setting(settings):
    if type(settings)is not dict or set(settings)!={'side_assignment'} or settings['side_assignment']not in ('marker_first','marker_second'):
        raise ValueError('settings must be exactly side_assignment=marker_first|marker_second')
    return settings['side_assignment']


def program(settings):
    return (BASE/('canonical.rkt'if setting(settings)=='marker_first'else'marker_second.rkt')).read_text()


def sample_input(seed,index):
    if type(seed)is not int or not 0<=seed<2**63 or type(index)is not int or index<0:
        raise ValueError('seed and index must be nonnegative exact integers')
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=TASK)
    rng=ctx.draw_rng('partition-scene');stress=index==103
    n=13 if stress else rng.randrange(5,7) if index in (0,100) else rng.randrange(7,10) if index==1 else rng.randrange(7,14)
    palette=list(range(10));rng.shuffle(palette);frame,bg,ink,ca,cb=palette[:5]
    if index in (0,1):
        ca,cb=sorted((ca,cb),reverse=index==1)
    kind={0:'diagonal',1:'bend',100:'axis',101:'diagonal',102:'bend',103:'zigzag'}.get(index,('axis','diagonal','bend','zigzag')[index%4])
    if kind=='diagonal':line={(r,r)for r in range(n)}
    elif kind=='axis':
        k=rng.randrange(2,n-2);line={(r,k)for r in range(n)}
    elif kind=='bend':
        k=n//2 if index==1 else rng.randrange(2,n-2)
        m=n//2 if index==1 else rng.randrange(2,n-2)
        line={(r,k)for r in range(m+1)}|{(m,c)for c in range(k,n)}
    else:
        k=n//3;k2=2*n//3;m=n//2
        line={(r,k)for r in range(m+1)}|{(m,c)for c in range(k,k2+1)}|{(r,k2)for r in range(m,n)}
    # Vary orientation before placing the singleton. Its side, not its absolute
    # location or the line's nominal type, chooses the source.
    turns=rng.randrange(4);mirror=rng.randrange(2)
    for _ in range(turns):line={(c,n-1-r)for r,c in line}
    if mirror:line={(r,n-1-c)for r,c in line}
    domain={(r,c)for r in range(n)for c in range(n)}
    regions=model.components(domain-line)
    if len(regions)!=2:raise RuntimeError('Constructed divider did not split the domain')
    marked=regions[1 if index%2==0 else 0]
    eligible=sorted(p for p in marked if min(max(abs(p[0]-r),abs(p[1]-c))for r,c in line)>1)
    if not eligible:raise RuntimeError('Hint would join the divider')
    hint=rng.choice(eligible)
    instruction=[[bg]*n for _ in range(n)]
    for r,c in line|{hint}:instruction[r][c]=ink
    first=[[ca if rng.random()<.45 else bg for _ in range(n)]for _ in range(n)]
    second=[[cb if rng.random()<.45 else bg for _ in range(n)]for _ in range(n)]
    # Teach overlay precedence AND fallback (not an always-first boundary rule).
    line_order=sorted(line)
    for (r,c),(a,b)in zip(line_order,((ca,cb),(bg,cb),(ca,bg),(bg,bg))):
        first[r][c]=a;second[r][c]=b
    # Treating the hint as divider geometry is wrong in each of the two settings.
    first[hint[0]][hint[1]],second[hint[0]][hint[1]]=(bg,cb)if index%2==0 else(ca,bg)
    protected=set(line_order[:4])|{hint}
    for region in regions:
        r,c=next(p for p in sorted(region)if p!=hint)
        first[r][c]=ca;second[r][c]=cb;protected.add((r,c))
    if index==1:
        # A bent separator must visibly disagree with its endpoint chord.
        start,end=min(line),max(line)
        def cross(p):return (end[0]-start[0])*(p[1]-start[1])-(end[1]-start[1])*(p[0]-start[0])
        sign=1 if cross(hint)>=0 else -1
        halfplane={p for p in domain-line if sign*cross(p)>=0}
        gap=sorted((marked^halfplane)-{hint})
        if not gap:raise RuntimeError('Bent teaching geometry aliases a straight cut')
        r,c=gap[0];first[r][c]=ca;second[r][c]=cb;protected.add((r,c))
    if index in (0,1):
        # Reverse visible area ordering across the minimum teaching prefix.
        low=n*n//3;high=2*n*n//3
        targets=(low,high)if index==0 else(high,low)
        for source,color,target in zip((first,second),(ca,cb),targets):
            fixed=sum(source[r][c]!=bg for r,c in protected)
            free=sorted(domain-protected);rng.shuffle(free);needed=target-fixed
            if not 0<=needed<=len(free):raise RuntimeError('Invalid teaching density target')
            for i,(r,c)in enumerate(free):source[r][c]=color if i<needed else bg
    panels=[instruction,first,second,[[bg]*n for _ in range(n)]]
    nr,nc=(2,2)if n>6 else rng.choice(((1,4),(4,1),(2,2)))
    h=nr*n+nr+1;w=nc*n+nc+1
    if stress:h=w=30
    grid=[[frame]*w for _ in range(h)]
    for i,panel in enumerate(panels):
        top=1+(i//nc)*(n+1);left=1+(i%nc)*(n+1)
        for r in range(n):
            for c in range(n):grid[top+r][left+c]=panel[r][c]
    data=model.analyze(grid)
    if set(data['selected'])!=marked:raise RuntimeError('Instruction extraction mismatch')
    return grid


def generate(seed,settings,demos,queries):
    mode=setting(settings)
    if type(demos)is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries)is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    def pair(index):
        g=sample_input(seed,index);return {'input':g,'output':model.solve(g,mode)}
    train=[pair(i)for i in range(demos)];bank=[pair(100+i)for i in range(4)]
    return {'train':train,'test':copy.deepcopy(bank[:queries]),'program_solution':program(settings),
            'settings':copy.deepcopy(settings),'seed':seed,'private':{'query_bank':bank}}


def public_view(episode,turn=0,presentation_seed=0):
    if type(turn)is not int or not 0<=turn<4:raise ValueError('turn must be 0..3')
    if type(presentation_seed)is not int:raise ValueError('presentation_seed must be an integer')
    bank=episode['private']['query_bank']
    if len(bank)!=4:raise ValueError('Four private queries required')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    train=[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])}for p in episode['train']]
    return {'train':train,'test':[{'input':copy.deepcopy(bank[order[turn]]['input'])}]}
