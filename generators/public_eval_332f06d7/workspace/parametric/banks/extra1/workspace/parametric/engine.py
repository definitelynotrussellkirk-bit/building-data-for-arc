"""Boat-footprint navigation, deterministic route tracing, and sampler."""
from __future__ import annotations
from collections import Counter, deque
from functools import lru_cache
import hashlib, json, random

VALUES=('move_only','trace_route')
RIVALS=('other_setting','move_to_goal','farthest_dead_end','point_boat','keep_old_boat','mark_all_reachable')
N4=((-1,0),(0,-1),(0,1),(1,0))


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}; bool is forbidden')
    return value


def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list
        or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0])
               or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular 1..30 exact-integer color grid')


def bbox(cells):
    cells=list(cells)
    if not cells:raise ValueError('Missing required colored rectangle')
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)


def rect(pos,bh,bw):
    r,c=pos
    return [(rr,cc) for rr in range(r,r+bh) for cc in range(c,c+bw)]


def _wall(g):
    colors={v for row in g for v in row}
    walls=colors-{0,1,2}
    if len(walls)!=1:raise ValueError('Expected exactly one wall color outside 0, 1, and 2')
    return next(iter(walls))


def _solid(g,cells,color):
    b=bbox(cells);expected=set(rect((b[0],b[1]),b[2]-b[0]+1,b[3]-b[1]+1))
    return set(cells)==expected and all(g[r][c]==color for r,c in expected)


def _valid_positions(g,bh,bw,bg):
    h,w=len(g),len(g[0]);out=[]
    for r in range(h-bh+1):
        for c in range(w-bw+1):
            if all(g[rr][cc]!=bg for rr,cc in rect((r,c),bh,bw)):out.append((r,c))
    return out


def _neighbors(p,allowed):
    r,c=p
    return [(r+dr,c+dc) for dr,dc in N4 if (r+dr,c+dc) in allowed]


def _graph(start,allowed):
    allowed=set(allowed)
    if start not in allowed:raise ValueError('Boat start is not a navigable placement')
    queue=deque([start]);parent={start:None};order=[]
    while queue:
        p=queue.popleft();order.append(p)
        for q in _neighbors(p,allowed):
            if q not in parent:parent[q]=p;queue.append(q)
    return order,parent


def _path(parent,end):
    path=[];p=end
    while p is not None:path.append(p);p=parent[p]
    return list(reversed(path))


def parse(g,bh_override=None,bw_override=None):
    grid_check(g);h,w=len(g),len(g[0])
    if h<3 or w<3:raise ValueError('Navigation grid must be at least 3x3')
    colors={v for row in g for v in row}
    if not {0,1,2}.issubset(colors):raise ValueError('Expected boat 0, corridor 1, and destination 2')
    bg=_wall(g)
    zero=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==0]
    goal_cells=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==2]
    zb=bbox(zero);gb=bbox(goal_cells)
    if not _solid(g,zero,0) or not _solid(g,goal_cells,2):
        raise ValueError('Boat and destination must each be one solid rectangle')
    actual_h,actual_w=zb[2]-zb[0]+1,zb[3]-zb[1]+1
    gh,gw=gb[2]-gb[0]+1,gb[3]-gb[1]+1
    if (actual_h,actual_w)!=(gh,gw):raise ValueError('Boat and destination rectangles must have equal dimensions')
    bh=actual_h if bh_override is None else bh_override
    bw=actual_w if bw_override is None else bw_override
    start=(zb[0],zb[1]);goal=(gb[0],gb[1])
    allowed=_valid_positions(g,bh,bw,bg);reachable,parent=_graph(start,allowed)
    rset=set(reachable)
    dead=[p for p in reachable if p!=start and len(_neighbors(p,rset))<=1]
    if not dead:dead=[start]
    selected=min(dead,key=lambda p:(abs(p[0]-goal[0])+abs(p[1]-goal[1]),p[0],p[1]))
    route=_path(parent,selected)
    return {'height':h,'width':w,'background':bg,'boat_height':actual_h,'boat_width':actual_w,
            'graph_height':bh,'graph_width':bw,'start':start,'goal':goal,'valid':allowed,
            'reachable':reachable,'parent':parent,'dead_ends':dead,'selected':selected,'route':route}


def _move(g,p,endpoint,restore=True):
    out=[row[:] for row in g]
    if restore:
        for r,c in rect(p['start'],p['boat_height'],p['boat_width']):out[r][c]=1
    for r,c in rect(endpoint,p['boat_height'],p['boat_width']):
        if 0<=r<p['height'] and 0<=c<p['width']:out[r][c]=0
    return out


def _trace(out,positions,p,endpoint):
    swept=set()
    for pos in positions:
        if pos==endpoint:continue
        swept.update(rect(pos,p['boat_height'],p['boat_width']))
    result=[row[:] for row in out]
    for r,c in swept:
        if 0<=r<p['height'] and 0<=c<p['width'] and result[r][c]==1:result[r][c]=9
    return result


def analyze(g):
    p=parse(g);rset=set(p['reachable'])
    edges=sum(len(_neighbors(x,rset)) for x in p['reachable'])//2
    return {'background':p['background'],'boat_height':p['boat_height'],'boat_width':p['boat_width'],
            'start':list(p['start']),'goal':list(p['goal']),'selected':list(p['selected']),
            'dead_ends':[list(x) for x in p['dead_ends']],
            'reachable':[list(x) for x in p['reachable']], 'route':[list(x) for x in p['route']],
            'reachable_edges':edges}


def solve(g,value='move_only',rival=None):
    if value not in VALUES:raise ValueError('Unknown finish setting')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    if rival=='other_setting':value='trace_route' if value=='move_only' else 'move_only'
    if rival=='point_boat':
        p=parse(g,1,1)
        # A point agent takes the reachable placement nearest the destination,
        # ignoring both boat clearance and the dead-end requirement.
        endpoint=min(p['reachable'],key=lambda x:(abs(x[0]-p['goal'][0])+abs(x[1]-p['goal'][1]),x))
        positions=_path(p['parent'],endpoint)
    else:
        p=parse(g);endpoint=p['selected'];positions=p['route']
    if rival=='move_to_goal':endpoint=p['goal'];positions=_path(p['parent'],endpoint) if endpoint in p['parent'] else [p['start'],endpoint]
    elif rival=='farthest_dead_end':
        endpoint=max(p['dead_ends'],key=lambda x:(abs(x[0]-p['goal'][0])+abs(x[1]-p['goal'][1]),-x[0],-x[1]))
        positions=_path(p['parent'],endpoint)
    out=_move(g,p,endpoint,restore=rival!='keep_old_boat')
    if value=='trace_route' or rival=='mark_all_reachable':
        positions=p['reachable'] if rival=='mark_all_reachable' else positions
        out=_trace(out,positions,p,endpoint)
    return out


def self_check(g):
    try:
        parse(g);solve(g,'move_only')
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []


def stream(seed,kind,index=0):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**63-1,'index')
    return random.Random(int.from_bytes(hashlib.sha256(f'332f06d7:{seed}:{kind}:{index}'.encode()).digest(),'big'))


def _paint_window(g,pos,k,color):
    for r,c in rect(pos,k,k):g[r][c]=color


def _transform(g,code):
    if code==0:return [row[:] for row in g]
    if code==1:return [list(reversed(row)) for row in g]
    if code==2:return list(reversed([row[:] for row in g]))
    if code==3:return [list(reversed(row)) for row in reversed(g)]
    if code==4:return [list(x) for x in zip(*g)]
    if code==5:return [list(reversed(x)) for x in zip(*g)]
    if code==6:return [list(x) for x in zip(*reversed(g))]
    if code==7:return [list(x) for x in zip(*[list(reversed(row)) for row in g])]
    raise ValueError('bad transform')


def _candidate(seed,index,kind,h,w,attempt):
    rng=stream(seed,kind,index*257+attempt)
    k=rng.choice([2,3,4])
    if min(h,w)<16 or k+12>min(h,w):raise ValueError('Canvas too small')
    g=[[3]*w for _ in range(h)]
    ur=1+rng.randrange(2);lc=1+rng.randrange(2)
    dr=h-k-2-rng.randrange(2);rc=w-k-2-rng.randrange(2)
    jc=max(lc+k+3,min(w//2-k//2+rng.choice([-1,0,1]),rc-k-3))
    jr=max(ur+k+2,min(h//2-k//2+rng.choice([-1,0,1]),dr-k-2))
    if not (ur<jr<dr and lc<jc<rc):raise ValueError('No room for navigation tree')
    # Union of width-k horizontal/vertical corridors. Their placement graph is
    # a cross-shaped tree rather than a point-agent maze.
    for c in range(lc,rc+1):_paint_window(g,(jr,c),k,1)
    for r in range(ur,dr+1):_paint_window(g,(r,jc),k,1)
    # Put the goal on a separate k-by-k island joined only by a one-cell bridge.
    gc=jc+k+2
    if gc+k>w-1:raise ValueError('Goal island does not fit')
    bridge_row=ur+rng.randrange(k)
    for c in range(jc+k,gc):g[bridge_row][c]=1
    _paint_window(g,(ur,gc),k,2)
    _paint_window(g,(jr,lc),k,0)
    choices=range(8) if h==w else range(4)
    return _transform(g,rng.choice(tuple(choices)))


def make_input(seed,index,kind='ordinary',stress=False,h=None,w=None):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**63-1,'index')
    if h is None or w is None:
        if stress:h=w=30
        else:
            sizes=((18,18),(20,22),(22,20),(24,24),(26,28),(28,26));h,w=sizes[index%len(sizes)]
    for attempt in range(128):
        try:
            g=_candidate(seed,index,kind,h,w,attempt);info=analyze(g)
            reachable={tuple(x) for x in info['reachable']};route={tuple(x) for x in info['route']}
            if tuple(info['goal']) in reachable or tuple(info['selected'])==tuple(info['goal']):continue
            if len(info['dead_ends'])<3 or len(reachable)<=len(route)+2:continue
            if info['reachable_edges']!=len(reachable)-1:continue
            if solve(g,'move_only')==solve(g,'trace_route'):continue
            return g
        except (ValueError,IndexError):continue
    raise ValueError('Bounded boat-navigation sampler exhausted')


@lru_cache(maxsize=128)
def input_bank(seed):
    integer(seed,0,2**63-1,'seed')
    demos=[make_input(seed,i,'demo') for i in range(6)]
    queries=[make_input(seed,i,'query',stress=i==3) for i in range(4)]
    packed=[json.dumps(g,separators=(',',':')) for g in demos+queries]
    if len(set(packed))!=len(packed):raise ValueError('Unexpected duplicate source input')
    for value in VALUES:
        gold=[solve(g,value) for g in demos[:2]]
        for rival in RIVALS:
            if all(solve(g,value,rival=rival)==y for g,y in zip(demos[:2],gold)):
                raise ValueError(f'Teaching prefix failed to reject {value}/{rival}')
    return tuple(packed[:6]),tuple(packed[6:])
