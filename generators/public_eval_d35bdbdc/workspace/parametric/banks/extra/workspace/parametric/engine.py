"""Wire-selected input-defined color pointers. No resources or runtime imports."""
from collections import Counter, deque
from copy import deepcopy
from functools import lru_cache
import random

D4 = ((-1,0),(1,0),(0,-1),(0,1))
D8 = tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c)
POLICIES = ('one_hop','follow_chain','raw_center','two_hops','three_hops',
            'keep_all','largest_two','body_color','minimum_center','maximum_center','reverse_lookup',
            'smallest_two','corner_two','first_two','last_two','touch_gray',
            'chain_largest_two','chain_smallest_two','chain_corner_two','chain_first_two','chain_last_two','chain_touch_gray',
            'cycle_zero','cycle_minimum')

def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or
        not 1<=len(g[0])<=30 or any(type(row) is not list or len(row)!=len(g[0]) or
        any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected rectangular 1..30 grid of exact integer ARC colors')

def parse(g):
    grid_check(g)
    wire={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==5}
    if not wire:raise ValueError('gray wire missing')
    def adjacent(p):
        r,c=p
        return [(r+dr,c+dc) for dr,dc in D8 if (r+dr,c+dc) in wire and
                (not dr or not dc or ((r+dr,c) not in wire and (r,c+dc) not in wire))]
    ends=sorted(p for p in wire if len(adjacent(p))==1)
    if len(ends)!=2:raise ValueError('exactly two wire endpoints required')
    seen={min(wire)};todo=list(seen)
    while todo:
        for q in adjacent(todo.pop()):
            if q not in seen:seen.add(q);todo.append(q)
    if seen!=wire:raise ValueError('wire is disconnected')
    unseen={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v not in (0,5)}
    beads=[]
    while unseen:
        p=min(unseen);unseen.remove(p);cells={p};todo=[p]
        while todo:
            r,c=todo.pop()
            for dr,dc in D4:
                q=r+dr,c+dc
                if q in unseen:unseen.remove(q);cells.add(q);todo.append(q)
        counts=Counter(g[r][c] for r,c in cells)
        body=sorted(counts,key=lambda v:(-counts[v],v))[0]
        other=[p for p in cells if g[p[0]][p[1]]!=body]
        if len(other)>1:raise ValueError('beads need a single distinct center or a uniform cross')
        if other:center=other[0]
        else:
            center=((min(r for r,c in cells)+max(r for r,c in cells))//2,
                    (min(c for r,c in cells)+max(c for r,c in cells))//2)
        if center not in cells:raise ValueError('bead center absent')
        beads.append({'cells':sorted(cells),'body':body,'center':center,'value':g[center[0]][center[1]]})
    if len({b['body'] for b in beads})!=len(beads):raise ValueError('body colors must identify distinct beads')
    candidates=[]
    for r,c in ends:
        candidates.append([i for i,b in enumerate(beads)
             if b['value'] in {x['body'] for x in beads} and
                (b['center'][0]==r or b['center'][1]==c) and
                any(abs(r-u)+abs(c-v)==1 for u,v in b['cells'])])
    matches={tuple(sorted((a,b))) for a in candidates[0] for b in candidates[1] if a!=b}
    if len(matches)!=1:raise ValueError('endpoint-to-bead assignment is not unique')
    return {'wire':sorted(wire),'ends':ends,'beads':beads,'selected':list(next(iter(matches)))}

def trace(value,mapping,steps=None):
    visited=[]
    while value in mapping and value not in visited and (steps is None or len(visited)<steps):
        visited.append(value);value=mapping[value]
    return value,visited

def predict(g,policy='one_hop'):
    if policy not in POLICIES:raise ValueError('unknown transfer policy')
    cert=parse(g);beads=cert['beads'];selected=cert['selected']
    mapping={b['body']:b['value'] for b in beads}
    selector=policy.removeprefix('chain_')
    if selector=='smallest_two':selected=sorted(range(len(beads)),key=lambda i:(len(beads[i]['cells']),i))[:2]
    if selector=='first_two':selected=list(range(min(2,len(beads))))
    if selector=='last_two':selected=list(range(max(0,len(beads)-2),len(beads)))
    if selector=='corner_two':
        def distance(i):
            r,c=beads[i]['center'];return min(r,len(g)-1-r)+min(c,len(g[0])-1-c)
        selected=sorted(range(len(beads)),key=lambda i:(distance(i),i))[:2]
    if selector=='touch_gray':selected=[i for i,b in enumerate(beads) if any(abs(r-u)+abs(c-v)==1 for r,c in b['cells'] for u,v in cert['wire'])]
    if selector=='keep_all':selected=list(range(len(beads)))
    if selector=='largest_two':selected=sorted(range(len(beads)),key=lambda i:(-len(beads[i]['cells']),i))[:2]
    out=[[5 if v==5 else 0 for v in row] for row in g]
    for i in selected:
        b=beads[i];value=b['value']
        if policy=='raw_center':new=value
        elif policy=='body_color':new=b['body']
        elif policy=='minimum_center':new=min(mapping.values())
        elif policy=='maximum_center':new=max(mapping.values())
        elif policy in ('cycle_zero','cycle_minimum'):
            new,visited=trace(value,mapping)
            if new in visited:new=0 if policy=='cycle_zero' else min(visited[visited.index(new):])
        elif policy=='reverse_lookup':new=next((k for k,v in sorted(mapping.items()) if v==value),value)
        else:
            steps=None if policy=='follow_chain' or policy.startswith('chain_') else (2 if policy=='two_hops' else 3 if policy=='three_hops' else 1)
            new=trace(value,mapping,steps)[0]
        for r,c in b['cells']:out[r][c]=g[r][c]
        r,c=b['center'];out[r][c]=new
    return out

def transform(g,pose):
    out=deepcopy(g)
    if pose>=4:out=[row[::-1] for row in out]
    for _ in range(pose%4):out=[list(row) for row in zip(*out[::-1])]
    return out

def _shortest_path(grid,start,end,blocked,rng):
    if start in blocked or end in blocked:return None
    h,w=len(grid),len(grid[0]);parent={start:None};queue=deque([start]);steps=list(D4);rng.shuffle(steps)
    while queue:
        p=queue.popleft()
        if p==end:
            result=[]
            while p is not None:result.append(p);p=parent[p]
            return result[::-1]
        for dr,dc in steps:
            q=(p[0]+dr,p[1]+dc)
            if 0<=q[0]<h and 0<=q[1]<w and not grid[q[0]][q[1]] and q not in blocked and q not in parent:
                parent[q]=p;queue.append(q)
    return None

def _route(grid,positions,radius,body,rng,diagonal):
    h,w=len(grid),len(grid[0])
    def ports(i):
        r,c=positions[i]
        return [(r+(radius+1)*dr,c+(radius+1)*dc) for dr,dc in D4
                if 0<=r+(radius+1)*dr<h and 0<=c+(radius+1)*dc<w and
                   grid[r+(radius+1)*dr][c+(radius+1)*dc]==0]
    starts,ends=ports(0),ports(1);vias=[p for i in range(2,6) for p in ports(i)]
    for attempt in range(160):
        start=rng.choice(starts);end=rng.choice(ends);via=rng.choice(vias)
        if len({start,end,via})!=3:continue
        first=_shortest_path(grid,start,via,{end},rng)
        if first is None:continue
        second=_shortest_path(grid,via,end,set(first[:-1]),rng)
        if second is None:continue
        path=first+second[1:]
        if len(path)<5:continue
        wire=set(path)
        if diagonal:
            # Remove only empty-corner turns, retaining the donor-contact waypoint.
            for k in range(2,len(path)-2):
                p=path[k];a=path[k-1];b=path[k+1]
                if (p!=via and abs(a[0]-b[0])==abs(a[1]-b[1])==1 and
                    not any(0<=p[0]+dr<h and 0<=p[1]+dc<w and grid[p[0]+dr][p[1]+dc] for dr,dc in D4)):
                    wire.discard(p)
        candidate=deepcopy(grid)
        for r,c in wire:candidate[r][c]=5
        try:cert=parse(candidate)
        except ValueError:continue
        selected={cert['beads'][i]['body'] for i in cert['selected']}
        touched={b['body'] for b in cert['beads'] if any(abs(r-u)+abs(c-v)==1 for r,c in b['cells'] for u,v in wire)}
        if selected==set(body[:2]) and touched-selected:return candidate
    raise ValueError('bounded wire routing exhausted')

GRAPH_PROFILES = ('mixed_cycles','acyclic','two_cycle','self_loop','receiver_cycle',
                  'shared_cycle','two_cycle','self_loop','receiver_cycle','acyclic')

def _scene(seed,index,attempt=0,graph_profile=None):
    rng=random.Random(f'd35bdbdc:scene:{seed}:{index}:{attempt}')
    large=index==9
    h,w=(30,30) if large else (rng.randint(14,20),rng.randint(15,24))
    radius=2 if large else 1
    left,right=(radius,radius),(radius,w-radius-1)
    positions=[left,right,(h//2,6 if large else 3),(h//2,w-7 if large else w-4),
               (h-radius-1,6 if large else 3),(h-radius-1,w-7 if large else w-4)]
    rng.shuffle(positions)
    colors=rng.sample([1,2,3,4,6,7,8,9],8);body=colors[:6];terminal=colors[6:]
    lengths=[(1,3),(0,4),(2,2),(3,1),(4,0),(1,2),(2,2),(4,0),(1,2),(1,3)][index]
    links={};pool=list(range(2,6));rng.shuffle(pool);cursor=0
    for endpoint,length in enumerate(lengths):
        chain=pool[cursor:cursor+length];cursor+=length
        if not chain:links[endpoint]=terminal[endpoint]
        else:
            links[endpoint]=body[chain[0]]
            for a,b in zip(chain,chain[1:]):links[a]=body[b]
            links[chain[-1]]=terminal[endpoint]
    if 0 in lengths:
        # A shared four-link chain gives one receiver depth four and the
        # other depth one without needing extra colors or dead receivers.
        for a,b in zip(pool,pool[1:]):links[a]=body[b]
        links[pool[-1]]=terminal[0]
        links[0]=body[pool[0]];links[1]=body[pool[-1]]
        lengths=(4,1)
    for i in range(6):links.setdefault(i,rng.choice(terminal))
    if graph_profile is None:graph_profile=GRAPH_PROFILES[index]
    if graph_profile not in set(GRAPH_PROFILES):raise ValueError('unknown pointer-graph profile')
    a,b,c,d=pool
    if graph_profile=='mixed_cycles':
        links={0:body[a],1:max(body[b],body[c]),a:body[a],b:body[c],c:body[b],d:terminal[0]}
    elif graph_profile=='two_cycle':
        links={0:body[a],1:body[c],a:body[b],b:body[a],c:body[d],d:terminal[1]}
    elif graph_profile=='self_loop':
        links={0:body[a],1:body[b],a:body[a],b:body[c],c:body[d],d:terminal[1]}
    elif graph_profile=='receiver_cycle':
        links={0:body[a],1:body[b],a:body[0],b:body[c],c:body[d],d:terminal[1]}
    elif graph_profile=='shared_cycle':
        links={0:body[a],1:body[b],a:body[b],b:body[a],c:terminal[0],d:terminal[1]}
    g=[[0]*w for _ in range(h)]
    for i,(r,c) in enumerate(positions):
        square=(i>=2) if index==0 else ((i<2) if index==1 else (large or rng.randrange(2)==0))
        for dr in range(-radius,radius+1):
            for dc in range(-radius,radius+1):
                if square or dr==0 or dc==0:g[r+dr][c+dc]=body[i]
        g[r][c]=links[i]
    g=_route(g,positions,radius,body,rng,diagonal=index%2==0)
    pose=rng.randrange(8);g=transform(g,pose)
    cert=parse(g)
    if len(cert['beads'])!=6 or len(cert['selected'])!=2:raise AssertionError('construction lost bead grammar')
    mapping={b['body']:b['value'] for b in cert['beads']}
    lengths=[len(trace(cert['beads'][i]['value'],mapping)[1]) for i in cert['selected']]
    return g,{'profile':index,'lengths':list(lengths),'graph_profile':graph_profile,'pose':pose,'large':large,
              'bead_shapes':'squares' if large else 'squares_and_crosses',
              'wire_length':len(cert['wire']),'selected_geometric_ranks':cert['selected']}

@lru_cache(maxsize=128)
def bank(seed):
    scenes=[_scene(seed,i) for i in range(10)]
    # Bounded declared-hypothesis lesson gate, not an assertion of universal
    # identifiability. Query count/prefix never changes this full-bank decision.
    for attempt in range(64):
        failures=[]
        for mode in ('one_hop','follow_chain'):
            desired=[predict(g,mode) for g,m in scenes]
            for rival in POLICIES:
                if all(predict(scenes[i][0],rival)==desired[i] for i in (0,1)) and any(
                    predict(scenes[i][0],rival)!=desired[i] for i in range(6,10)):
                    failures.append((mode,rival))
        if not failures:break
        scenes[0]=_scene(seed,0,attempt+1);scenes[1]=_scene(seed,1,attempt+1)
    else:raise ValueError('bounded distinguishing-lesson construction exhausted')
    if len({str(g) for g,m in scenes})!=10:raise ValueError('duplicate bank input')
    return scenes
