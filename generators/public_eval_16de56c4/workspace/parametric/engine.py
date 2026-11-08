"""Periodic edge-seeded rays for public evaluation parent 16de56c4.

Each active line has two same-color seeds, the first at a common canvas edge.
Their separation is the period. A different-color marker beyond the second
seed triggers only when it lies on that lattice. A hit recolors the complete
run, including seeds; the canonical rule stops there. Off-lattice markers stay
unchanged and do not stop propagation. The alternative continues after a hit.
This module is self-contained; native engine.py is a tested exact snapshot.
"""
import random

RULE_TASK_ID = 'ee_16de56c4'
TASK_ID = 'public_eval_16de56c4'
VERSION = '1.0.0'
SETTINGS = ('stop_at_hit','continue_after_hit')


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid_check(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
        or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected rectangular 1..30 grid with exact integer colors')


def coordinate(side,line,offset,height,width):
    if side==0:return line,offset
    if side==1:return line,width-1-offset
    if side==2:return offset,line
    if side==3:return height-1-offset,line
    raise ValueError('side must be left/right/top/bottom (0..3)')


def analyze(grid):
    """Find the unique common source edge and derive periods and phase hits."""
    grid_check(grid);h,w=len(grid),len(grid[0]);candidates=[]
    for side in range(4):
        length,cross=(w,h) if side<2 else (h,w)
        rays=[];valid=True
        for line in range(cross):
            occupied=[]
            for offset in range(length):
                r,c=coordinate(side,line,offset,h,w);value=grid[r][c]
                if value:occupied.append((offset,value))
            if not occupied:continue
            if (len(occupied) not in (2,3) or occupied[0][0]!=0
                or occupied[0][1]!=occupied[1][1]
                or (len(occupied)==3 and occupied[2][1]==occupied[0][1])):
                valid=False;break
            spacing=occupied[1][0]
            marker=list(occupied[2]) if len(occupied)==3 else None
            hit=marker[:] if marker is not None and marker[0]%spacing==0 else None
            rays.append({'line':line,'spacing':spacing,'color':occupied[0][1],'marker':marker,'hit':hit})
        if valid and rays:candidates.append({'side':side,'length':length,'cross_length':cross,'rays':rays})
    if len(candidates)!=1:
        raise ValueError('exactly one source edge with paired seeds and at most one subsequent marker is required')
    return candidates[0]


def render(grid,plan,extent='stop_at_hit'):
    """Consume decoded lattice hits to choose color and stopping endpoint."""
    if extent not in SETTINGS:raise ValueError('invalid extent')
    out=[row[:] for row in grid];h,w=len(grid),len(grid[0])
    for ray in plan['rays']:
        hit=ray['hit'];end=hit[0] if hit is not None and extent=='stop_at_hit' else plan['length']-1
        color=hit[1] if hit is not None else ray['color']
        for t in range(0,end+1,ray['spacing']):
            r,c=coordinate(plan['side'],ray['line'],t,h,w);out[r][c]=color
    return out


def solve(grid,mode='stop_at_hit'):
    if type(mode) is not str or mode not in SETTINGS:raise ValueError('invalid extent')
    return render(grid,analyze(grid),mode)


def rule_mirror(grid):return solve(grid,'stop_at_hit')


def _make(rng,h,w,side,stress=False):
    length,cross=(w,h) if side<2 else (h,w)
    n=rng.randint(12,16) if stress else rng.randint(4,min(7,cross-2))
    if stress:lines=sorted([0,cross-1]+rng.sample(list(range(1,cross-1)),n-2))
    else:lines=sorted(rng.sample(list(range(1,cross-1)),n))
    # The first four roles guarantee a true hit, an off-lattice distractor,
    # a longer-period hit and a markerless ray in every teaching scene.
    profiles=[(1,'hit'),(2,'miss'),(3,'hit'),(rng.choice((2,3)),None)]
    if stress:profiles += [(1,None)]*6
    while len(profiles)<n:
        spacing=rng.randint(1,min(5,(length-2)//2))
        profiles.append((spacing,rng.choice(('hit','miss',None)) if spacing>1 else rng.choice(('hit',None))))
    rng.shuffle(profiles)
    if stress:
        # Full unit-period boundary rays give substantive coverage on all edges.
        profiles[0]=profiles[-1]=(1,None)
    grid=[[0]*w for _ in range(h)];previous=0
    for line,(spacing,kind) in zip(lines,profiles):
        color=rng.choice([v for v in range(1,10) if v!=previous]);previous=color
        def put(offset,value):
            r,c=coordinate(side,line,offset,h,w);grid[r][c]=value
        put(0,color);put(spacing,color)
        if kind is not None:
            choices=[t for t in range(spacing+1,length-2) if (t%spacing==0)==(kind=='hit')]
            if not choices:raise ValueError('constructor has no lawful control position')
            pos=rng.choice(choices);marker_color=rng.choice([v for v in range(1,10) if v!=color])
            put(pos,marker_color)
    plan=analyze(grid)
    if plan['side']!=side:raise ValueError('constructor produced ambiguous source edge')
    return grid


def scene(seed,index,kind):
    integer(seed,0,2**63-1,'seed')
    if kind not in ('demo','query'):raise ValueError('kind must be demo/query')
    integer(index,0,5 if kind=='demo' else 3,'index')
    rng=random.Random(f'16de56c4:v1:{seed}:{kind}:{index}')
    sizes=((13,15),(17,19),(20,16),(15,23),(23,17),(26,22)) if kind=='demo' else ((14,16),(19,23),(24,27),(30,30))
    h,w=sizes[index]
    if rng.randrange(2):h,w=w,h
    orientation=random.Random(f'16de56c4:orientation:{seed}');base=orientation.randrange(4)
    if kind=='demo':side=base if index==0 else base^2 if index==1 else rng.randrange(4)
    else:
        order=list(range(4));orientation.shuffle(order);side=order[index]
    return _make(rng,h,w,side,stress=kind=='query' and index==3)


def generate(seed=0,sample_index=0,difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**63-1,'sample_index')
    if difficulty is None:difficulty='medium'
    if difficulty not in ('easy','medium','hard','mixed'):raise ValueError('unsupported difficulty')
    rng=random.Random(f'16de56c4:base:{seed}:{sample_index}:{difficulty}')
    if difficulty=='mixed':difficulty=rng.choice(('easy','medium','hard'))
    h,w={'easy':(9,11),'medium':(19,23),'hard':(30,30)}[difficulty]
    if rng.randrange(2):h,w=w,h
    return _make(rng,h,w,rng.randrange(4),stress=difficulty=='hard')


def self_check(grid,difficulty=None):
    try:analyze(grid)
    except (ValueError,TypeError) as exc:return [str(exc)]
    return []
