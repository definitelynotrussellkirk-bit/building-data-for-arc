"""Independent colored-corridor marker traces with explicit guidance state."""
from __future__ import annotations
from functools import lru_cache
import hashlib
import random

SETTINGS=('adaptive','initial')
RIVALS=('other_setting','straight_only','turn_any','clockwise_only',
        'counterclockwise_only','first_marker_only','ignore_entrance_color',
        'paint_trail','fixed_gate2','two_turn_budget')


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an integer in {lo}..{hi}; booleans forbidden')
    return value


def setting(value):
    if type(value) is not dict or set(value)!={'guidance'} or type(value['guidance']) is not str or value['guidance'] not in SETTINGS:
        raise ValueError('Expected exactly guidance=adaptive|initial')
    return value['guidance']


def checked_grid(grid):
    if (type(grid) is not list or not 3<=len(grid)<=30 or type(grid[0]) is not list or not 3<=len(grid[0])<=30
        or any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected rectangular 3..30 exact-integer grid')
    if any(v==6 for row in grid for v in row[1:]):raise ValueError('Input markers must be in the leftmost column')
    return grid


def entrances(grid,variant=None):
    H,W=len(grid),len(grid[0]);result=[]
    for r in range(1,H-1):
        if grid[r][0]!=6:continue
        for c in range(1,W):
            a,b,z=grid[r-1][c],grid[r+1][c],grid[r][c]
            if a!=7 or b!=7 or z!=7:
                gate=None
                if z==7:
                    if a==b and a not in (6,7):gate=a
                    elif variant=='ignore_entrance_color':
                        gate=a if a not in (6,7) else b if b not in (6,7) else None
                if gate is not None:result.append((r,gate))
                break
    return result


def routes(grid,guidance,*,variant=None):
    checked_grid(grid)
    if guidance not in SETTINGS:raise ValueError('Unknown guidance')
    H,W=len(grid),len(grid[0]);results=[]
    for source,initial in entrances(grid,variant):
        rr,cc,dr,dc=source,0,0,1;color=2 if variant=='fixed_gate2' else initial
        seen=set();trail=[];turns=[];handoffs=[]
        while True:
            state=(rr,cc,dr,dc,color)
            if state in seen:break
            seen.add(state);trail.append([rr,cc])
            sides=[]
            for ar,ac in [(-dc,dr),(dc,-dr)]:
                r,c=rr+ar,cc+ac;sides.append(grid[r][c] if 0<=r<H and 0<=c<W else 7)
            if guidance=='adaptive' and variant!='fixed_gate2' and sides[0]==sides[1] and sides[0] not in (6,7):
                if color!=sides[0]:handoffs.append({'position':[rr,cc],'from':color,'to':sides[0]})
                color=sides[0]
            nr,nc=rr+dr,cc+dc
            if not (0<=nr<H and 0<=nc<W):break
            value=grid[nr][nc]
            if value==7:rr,cc=nr,nc;continue
            if variant=='straight_only' or (value!=color and variant!='turn_any'):break
            options=[]
            for ar,ac in [(-dc,dr),(dc,-dr)]:
                r,c=rr+ar,cc+ac
                if 0<=r<H and 0<=c<W and grid[r][c]==7:options.append((ar,ac))
            if len(options)!=1:break
            if variant=='two_turn_budget' and len(turns)>=2:break
            ar,ac=options[0]
            if variant=='clockwise_only' and (ar,ac)!=(dc,-dr):break
            if variant=='counterclockwise_only' and (ar,ac)!=(-dc,dr):break
            turns.append([rr,cc]);dr,dc=ar,ac
        results.append({'source':[source,0],'initial_guidance':initial,'terminal_guidance':color,
                        'endpoint':[rr,cc],'trail':trail,'turns':turns,'handoffs':handoffs})
    return results[:1] if variant=='first_marker_only' else results


def solve(grid,guidance,*,variant=None):
    traces=routes(grid,guidance,variant=variant);out=[row[:] for row in grid]
    # Trace every marker against immutable input, then apply writes simultaneously.
    for t in traces:out[t['source'][0]][0]=7
    for t in traces:
        positions=t['trail'] if variant=='paint_trail' else [t['endpoint']]
        for r,c in positions:out[r][c]=6
    return out


def rival(grid,guidance,name):
    if name not in RIVALS:raise ValueError('Unknown rival')
    if name=='other_setting':return solve(grid,SETTINGS[1-SETTINGS.index(guidance)])
    return solve(grid,guidance,variant=name)


def rng(seed,label):
    return random.Random(int.from_bytes(hashlib.sha256(f'9bbf930d:{seed}:{label}'.encode()).digest(),'big'))


def polyline(vertices):
    result=[vertices[0]]
    for target in vertices[1:]:
        r,c=result[-1];tr,tc=target
        if r!=tr and c!=tc:raise ValueError('Polyline legs must be axis-aligned')
        dr=(tr>r)-(tr<r);dc=(tc>c)-(tc<c)
        while (r,c)!=(tr,tc):r+=dr;c+=dc;result.append((r,c))
    if len(set(result))!=len(result):raise ValueError('Construction must not self-intersect')
    return result


def scene(seed,label,shape,*,stress=False,long_route=False):
    H,W=shape;randomizer=rng(seed,label);colors=randomizer.sample([0,1,2,3,4,5,8,9],6)
    a,b,c,d,e,f=colors;top=randomizer.choice([2,3]);x1=randomizer.randint(W//2,W-5)
    x2=randomizer.randint(4,W//3);lower=H-4;target=W-randomizer.choice([3,4])
    if stress or long_route:
        top=3;x1=randomizer.randint(W//2,W-7)
        first=polyline([(top,0),(top,x1),(top+4,x1),(top+4,W-3),(1,W-3),(1,W-1)])
    else:
        first=polyline([(top,0),(top,x1),(top+4,x1),(top+4,W-1)])
    second=polyline([(lower,0),(lower,x2),(lower-4,x2),(lower-4,target)])
    paths=[first,second];grid=[[7]*W for _ in range(H)]
    for row in grid:row[0]=6
    for path,old,new,turn in [(first,a,b,x1),(second,c,d,x2)]:
        path_set=set(path)
        for i,(r,k) in enumerate(path):
            color=old if i<=turn+1 else new
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                rr,cc=r+dr,k+dc
                if 0<=rr<H and 2<=cc<W and (rr,cc) not in path_set:grid[rr][cc]=color
    for path in paths:
        for r,k in path:
            if k:grid[r][k]=7
    # A foreign obstacle with an open turn: wrong 'turn at any color' is exposed.
    end_r,end_c=second[-1];grid[end_r][end_c+1]=e;grid[end_r-1][end_c]=7
    # Unequal rails do not activate the magenta marker between them.
    for k in range(2,W-1):grid[9][k]=e;grid[11][k]=f
    # Optional straight control route: unlike both handoff routes, no turn is needed.
    if stress or randomizer.choice([False,True]):
        for k in range(2,W):grid[H-3][k]=c;grid[H-1][k]=c
    if randomizer.choice([False,True]):grid=grid[::-1]
    return grid


@lru_cache(maxsize=64)
def input_bank(seed):
    integer(seed,0,2**63-1,'seed')
    demo_shapes=[(22,20),(23,21),(24,22),(25,23),(26,24),(27,25)]
    query_shapes=[(24,28),(28,24),(29,29),(30,30)]
    for attempt in range(32):
        train=[scene(seed,f'demo:{attempt}:{i}',shape,long_route=(i%2==0)) for i,shape in enumerate(demo_shapes)]
        if all(any(rival(g,s,name)!=solve(g,s) for g in train[:2]) for s in SETTINGS for name in RIVALS
               if not (s=='initial' and name=='two_turn_budget')):break
    else:raise ValueError('No two-demo certificate within 32 constructions')
    test=[scene(seed,f'query:{i}',shape,stress=(i==3)) for i,shape in enumerate(query_shapes)]
    rng(seed,'presentation').shuffle(test)
    freeze=lambda gs:tuple(tuple(tuple(row) for row in g) for g in gs)
    return freeze(train),freeze(test)


def grids(seed):
    train,test=input_bank(seed)
    return [[list(row) for row in g] for g in train],[[list(row) for row in g] for g in test]
