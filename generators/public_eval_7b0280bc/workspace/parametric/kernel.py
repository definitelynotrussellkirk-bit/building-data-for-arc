"""Self-contained geometric graph sampler and independent Python rule mirror.

Squares are graph nodes; each eight-connected path-color component is an edge.
Two squares of the rarer node color are the endpoints. The canonical metric is
edge count, NOT physical length. The variant minimizes path-component ink.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import heapq
import random

GENERATOR_ID='public_eval_7b0280bc'
TASK_ID=GENERATOR_ID
RULE_TASK_ID='ee_7b0280bc'
VERSION='1.0.0'
SUMMARY='Infer the geometric graph and recolor the minimum-hop route between the two endpoint squares.'
EXAMPLES_NEEDED=2
INVARIANTS=['four colors excluding the output colors 3 and 5', 'two endpoint squares and at least three ordinary squares', 'each eight-connected pipe component joins exactly two nodes', 'positive edge weights and connected endpoints']
AXES={'grid_h':{'type':'int','valid':'18..30','default':'18..30'},'grid_w':{'type':'int','valid':'18..30','default':'18..30'}}


def integer(v,name,low=0,high=2**63-1):
    if type(v) is not int or not low<=v<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return v


def check_grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:raise ValueError('grid dimensions must be 1..30')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):raise ValueError('rectangular exact integer grid required')


def components(cells,diagonal=True):
    todo=set(cells);answer=[]
    delta=[(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr or dc) and (diagonal or abs(dr)+abs(dc)==1)]
    while todo:
        p=min(todo);todo.remove(p);stack=[p];part=[]
        while stack:
            r,c=stack.pop();part.append((r,c))
            for dr,dc in delta:
                q=(r+dr,c+dc)
                if q in todo:todo.remove(q);stack.append(q)
        answer.append(sorted(part))
    return answer


def _square(cells):
    rs=[r for r,c in cells];cs=[c for r,c in cells]
    height=max(rs)-min(rs)+1;width=max(cs)-min(cs)+1
    return height==width and height>=2 and len(cells)==height*width


def analyze(g):
    check_grid(g)
    counts=Counter(v for row in g for v in row)
    if len(counts)!=4:raise ValueError('exactly four input colors required')
    bg=min(counts,key=lambda k:(-counts[k],k))
    grouped={k:components((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==k) for k in counts if k!=bg}
    pipe_colors=[k for k,parts in grouped.items() if any(not _square(p) for p in parts)]
    if len(pipe_colors)!=1:raise ValueError('path color is not uniquely structurally identifiable')
    pipe=pipe_colors[0]
    nodes=sorted([{'color':k,'cells':p} for k,parts in grouped.items() if k!=pipe for p in parts],key=lambda n:n['cells'][0])
    node_counts=Counter(n['color'] for n in nodes)
    endpoint_colors=[k for k,count in node_counts.items() if count==2]
    if len(endpoint_colors)!=1 or len(node_counts)!=2:raise ValueError('need one unique two-square endpoint color')
    endpoints=[i for i,n in enumerate(nodes) if n['color']==endpoint_colors[0]]
    occupied={cell:i for i,n in enumerate(nodes) for cell in n['cells']}
    edges=[]
    for part in grouped[pipe]:
        touching=set()
        for r,c in part:
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if (r+dr,c+dc) in occupied:touching.add(occupied[r+dr,c+dc])
        if len(touching)!=2:raise ValueError('each pipe component must join exactly two squares')
        edges.append({'nodes':tuple(sorted(touching)),'cells':part})
    return {'background':bg,'pipe_color':pipe,'nodes':nodes,'edges':edges,'endpoints':endpoints}


def choose_route(graph,metric):
    if metric not in ('fewest_edges','least_ink'):raise ValueError('unknown route metric')
    start,end=graph['endpoints'];queue=[(0,(start,),())];visited=set()
    while queue:
        cost,path,edge_ids=heapq.heappop(queue);node=path[-1]
        if node in visited:continue
        if node==end:return {'cost':cost,'nodes':list(path),'edges':list(edge_ids)}
        visited.add(node)
        for i,edge in enumerate(graph['edges']):
            a,b=edge['nodes']
            if node not in (a,b):continue
            nxt=b if node==a else a
            if nxt in visited:continue
            weight=1 if metric=='fewest_edges' else len(edge['cells'])
            heapq.heappush(queue,(cost+weight,path+(nxt,),edge_ids+(i,)))
    raise ValueError('endpoint squares are disconnected')


def paint(g,graph,route):
    out=[row[:] for row in g]
    for i in route['edges']:
        for r,c in graph['edges'][i]['cells']:out[r][c]=5
    for i in route['nodes'][1:-1]:
        for r,c in graph['nodes'][i]['cells']:out[r][c]=3
    return out


def solve(g,metric='fewest_edges'):
    graph=analyze(g)
    return paint(g,graph,choose_route(graph,metric))


def _transform(g,code):
    a=[row[:] for row in g]
    if code&4:a=[list(row) for row in zip(*a)]
    if code&2:a=a[::-1]
    if code&1:a=[row[::-1] for row in a]
    return a


def _line(a,b):
    r,c=a;dr=b[0]-r;dc=b[1]-c
    if dr and dc and abs(dr)!=abs(dc):raise ValueError('segments must be axis aligned or 45 degrees')
    count=max(abs(dr),abs(dc));sr=(dr>0)-(dr<0);sc=(dc>0)-(dc<0)
    return [(r+i*sr,c+i*sc) for i in range(count+1)]


def _draw(seed,index,h,w):
    rng=random.Random(int.from_bytes(hashlib.sha256(f'{VERSION}:{seed}:{index}'.encode()).digest(),'big'))
    bg,pipe,normal,endpoint=rng.sample([0,1,2,4,6,7,8,9],4)
    side=3 if min(h,w)>=26 else 2;thick=side-1
    stress=(h,w)==(30,30)
    top=0 if stress else rng.randrange(2)
    left=0 if stress else rng.randrange(2)
    right=w-side if stress else w-side-rng.randrange(2)
    mid=h//2+1;low=mid+4
    agreement=index%7==1
    if agreement:
        top=5;mid=max(9,h//3+2);low=h-side
    middle=(left+right)//2;quarter=max(side+1,(right-left)//4)
    upper_count=1+index%2
    lower_count=max(2+index%3,upper_count+1)
    if agreement:lower_count=3
    origins={'S':(mid,left),'T':(mid,right),'U':(top,middle),
             'D':(max(mid-4,top+side+2),middle)}
    lower_names=[f'L{i}' for i in range(lower_count)]
    for i,name in enumerate(lower_names,1):
        origins[name]=(low,left+(right-left)*i//(lower_count+1))
    # Ports use the upper/left part of each square. A final separating row
    # prevents degree-three nodes being bypassed by an eight-connected corner.
    chamfer=1+index%2
    routes=[('S','U',[origins['S'],(top+chamfer,left),(top,left+chamfer),origins['U']]),
            ('U','T',[origins['U'],(top,right-chamfer),(top+chamfer,right),origins['T']]),
            ('S',lower_names[0],[origins['S'],(low,left),origins[lower_names[0]]]),
            (lower_names[-1],'T',[origins[lower_names[-1]],(low,right),origins['T']]),
            ('U','D',[origins['U'],origins['D']])]
    for a,b in zip(lower_names,lower_names[1:]):routes.append((a,b,[origins[a],origins[b]]))
    if upper_count==2:
        origins['V']=(top,(left+middle)//2)
        routes[0:1]=[('S','V',[origins['S'],(top+chamfer,left),(top,left+chamfer),origins['V']]),
                     ('V','U',[origins['V'],origins['U']])]
    if agreement:
        # The cross-link creates four endpoint routes, including alternatives
        # before AND after the correct route in node reading order. Lower
        # horizontal pipes use the squares' bottom ports so the top cross-link
        # does not bypass a square via eight-connected corner contact.
        replacement=[]
        for a,b,polyline in routes:
            if a in lower_names or b in lower_names:
                polyline=[(r+side-1 if r==low else r,c) for r,c in polyline]
            replacement.append((a,b,polyline))
        routes=replacement
        routes.append(('D','L1',[origins['D'],origins['L1']]))
    if h-low-2*side>=2:
        attach=lower_names[len(lower_names)//2]
        origins['B']=(h-side,origins[attach][1])
        routes.append((attach,'B',[origins[attach],origins['B']]))
    g=[[bg]*w for _ in range(h)]
    for a,b,polyline in routes:
        for p,q in zip(polyline,polyline[1:]):
            for r,c in _line(p,q):
                for dr in range(thick):
                    for dc in range(thick):
                        if 0<=r+dr<h and 0<=c+dc<w:g[r+dr][c+dc]=pipe
    for name,(r,c) in origins.items():
        for dr in range(side):
            for dc in range(side):g[r+dr][c+dc]=endpoint if name in ('S','T') else normal
    graph=analyze(g)
    if len(graph['nodes'])!=len(origins) or len(graph['edges'])!=len(routes):raise ValueError('geometric graph construction merged components')
    labels={pos:name for name,pos in origins.items()}
    inferred={frozenset(labels[graph['nodes'][i]['cells'][0]] for i in edge['nodes']) for edge in graph['edges']}
    if inferred!={frozenset((a,b)) for a,b,_ in routes}:raise ValueError('geometric graph incidence changed')
    agrees=choose_route(graph,'fewest_edges')['edges']==choose_route(graph,'least_ink')['edges']
    if agrees!=agreement:raise ValueError('route-metric teaching relation changed')
    if agreement:
        # Select a size-preserving view where the correct route is not the
        # first or last complete node-reading-order route. This is a finite
        # teaching constraint, independent of the episode's hidden setting.
        codes=list(range(4));rng.shuffle(codes)
        for code in codes:
            candidate=_transform(g,code);view=analyze(candidate)
            start,end=view['endpoints'];paths=[]
            def walk(node,path):
                if node==end:
                    paths.append(path);return
                for edge in view['edges']:
                    if node in edge['nodes']:
                        nxt=next(i for i in edge['nodes'] if i!=node)
                        if nxt not in path:walk(nxt,path+[nxt])
            walk(start,[start])
            chosen=choose_route(view,'fewest_edges')['nodes']
            if min(paths)<chosen<max(paths):return candidate
        raise ValueError('agreement teaching view lacks an interior-order route')
    # Adjacent demonstration indices change the geometric side of the choice.
    phase=int.from_bytes(hashlib.sha256(f'orientation:{seed}'.encode()).digest(),'big')%8
    return _transform(g,(phase+3*index)%8)


def generate(seed,sample_index,*,difficulty=None,**overrides):
    integer(seed,'seed');integer(sample_index,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('unknown axes')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'dim:{seed}:{sample_index}'.encode()).digest(),'big'))
    h=overrides.get('grid_h',rng.randrange(18,31));w=overrides.get('grid_w',rng.randrange(18,31))
    integer(h,'grid_h',18,30);integer(w,'grid_w',18,30)
    g=_draw(seed,sample_index,h,w)
    if (len(g),len(g[0]))!=(h,w):g=[list(row) for row in zip(*g)]
    return g


def self_check(grid,*,difficulty=None,meta=None):
    try:
        graph=analyze(grid)
        if set(v for row in grid for v in row)&{3,5}:return ['input uses output-only colors']
        choose_route(graph,'fewest_edges');choose_route(graph,'least_ink')
        return []
    except (ValueError,TypeError,IndexError) as error:return [str(error)]
