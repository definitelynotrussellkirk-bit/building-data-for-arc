"""Translation-only red-connector assembly; native resources are adjacent.

The canonical solver searches geometry, never an answer bank. The independent
constructive sampler retains known placements and the CSP checks uniqueness.
"""
from __future__ import annotations
from collections import deque
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import random

HERE=Path(__file__).resolve().parent
PARAMETERS={'assembly_policy':['assemble','deepest_piece']}
DEFAULT={'assembly_policy':'assemble'}
BASE_RIVALS=('assemble','largest_original','smallest_original','most_ports','last_input','shallowest','euclidean','all_movers')
RIVAL_NAMES=BASE_RIVALS+('longest_path',)

def _settings(settings):
    if type(settings) is not dict or set(settings)!=set(PARAMETERS) or type(settings['assembly_policy']) is not str or settings['assembly_policy'] not in PARAMETERS['assembly_policy']:
        raise ValueError('settings must name a declared assembly_policy')
    return settings['assembly_policy']

def program(settings):
    policy=_settings(settings)
    source=(HERE/'canonical.rkt').read_text()
    return source if policy=='assemble' else source.replace('(define output-policy "assemble")',f'(define output-policy "{policy}")',1)

def rival_programs():
    source=program(DEFAULT)
    result={p:source.replace('(define output-policy "assemble")',f'(define output-policy "{p}")',1)
            for p in BASE_RIVALS}
    # Keep the canonical reference byte-identical; only this counterfactual
    # replaces shortest-path BFS by longest simple-path distances.
    start=source.index('     (define (graph-depths entries)')
    end=source.index('     (define (top-left piece)',start)
    wrong_depths="""     (define (graph-depths entries)
       (define (walk current seen depth)
         (cons (list (first current) depth)
           (append-map
             (lambda (p) (walk p (cons (first p) seen) (+ depth 1)))
             (filter (lambda (p) (and (not (member (first p) seen)) (joined? current p))) entries))))
       (define visits (walk anchor (list anchor-id) 0))
       (for/list ((p entries))
         (list (first p) (apply max (map second (filter (lambda (v) (= (first v) (first p))) visits))))))
"""
    wrong=source[:start]+wrong_depths+source[end:]
    result['longest_path']=wrong.replace('(define output-policy "assemble")','(define output-policy "deepest_piece")',1)
    return result

def _grid(grid):
    if type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('expected rectangular integer grid in 1..30')

def _pieces(grid):
    unseen={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    pieces=[]
    while unseen:
        start=min(unseen);unseen.remove(start);stack=[start];component={}
        while stack:
            r,c=stack.pop();component[r,c]=grid[r][c]
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    q=r+dr,c+dc
                    if q in unseen:unseen.remove(q);stack.append(q)
        pieces.append(component)
    return pieces

def solve(grid, *, max_solutions=2):
    """Return the unique placed pieces and contact-graph depths or reject.

    Minimum-remaining-values backtracking pairs every red cell exactly twice;
    bodies cannot overlap and no component may leave the canvas. Unlike a
    face-normal heuristic this also admits the official corner contact.
    """
    _grid(grid);h,w=len(grid),len(grid[0]);pieces=_pieces(grid)
    anchors=[i for i,p in enumerate(pieces) if 4 in p.values()]
    if len(anchors)!=1:raise ValueError('exactly one yellow anchor required')
    anchor=anchors[0];ports=[{p for p,v in piece.items() if v==2} for piece in pieces]
    if any(not pp for pp in ports):raise ValueError('every piece needs a red connector')
    found=[];visited=set();node_count=0
    def search(placed,board,unpaired):
        nonlocal node_count
        node_count+=1
        if node_count>100000:raise ValueError('assembly search node cap exceeded')
        state=tuple(sorted((i,d) for i,d in placed.items()))
        if state in visited:return
        visited.add(state)
        if len(placed)==len(pieces):
            if not unpaired:found.append(dict(placed))
            return
        if not unpaired:return
        best=None
        for target in sorted(unpaired):
            choices=[]
            for i,piece in enumerate(pieces):
                if i in placed:continue
                for port in sorted(ports[i]):
                    dr,dc=target[0]-port[0],target[1]-port[1]
                    shifted={(r+dr,c+dc):v for (r,c),v in piece.items()}
                    if any(not(0<=r<h and 0<=c<w) for r,c in shifted):continue
                    if any(p in board and not(v==2 and board[p]==2 and p in unpaired) for p,v in shifted.items()):continue
                    new_ports={(r+dr,c+dc) for r,c in ports[i]}
                    choices.append((i,(dr,dc),shifted,new_ports))
            if best is None or len(choices)<len(best):best=choices
            if not best:return
        for i,delta,shifted,new_ports in best:
            search(placed|{i:delta},board|shifted,unpaired^new_ports)
            if len(found)>=max_solutions:return
    search({anchor:(0,0)},dict(pieces[anchor]),ports[anchor])
    if not found:raise ValueError('no complete assembly')
    if len(found)>1:raise ValueError('ambiguous assembly')
    offsets=found[0]
    placed=[{(r+offsets[i][0],c+offsets[i][1]):v for (r,c),v in piece.items()} for i,piece in enumerate(pieces)]
    final_ports=[{p for p,v in piece.items() if v==2} for piece in placed]
    graph=[[j for j in range(len(pieces)) if j!=i and final_ports[i]&final_ports[j]] for i in range(len(pieces))]
    depths=[-1]*len(pieces);depths[anchor]=0;todo=deque([anchor])
    while todo:
        i=todo.popleft()
        for j in graph[i]:
            if depths[j]<0:depths[j]=depths[i]+1;todo.append(j)
    output=[[0]*w for _ in range(h)]
    for piece in placed:
        for (r,c),v in piece.items():output[r][c]=v
    return {'output':output,'pieces':placed,'anchor':anchor,'depths':depths,'graph':graph,'offsets':[list(offsets[i]) for i in range(len(pieces))], 'search_nodes':node_count}

def predict(grid,policy='assemble',*,certificate=None):
    cert=solve(grid) if certificate is None else certificate
    out=deepcopy(cert['output']);moving=[i for i in range(len(cert['pieces'])) if i!=cert['anchor']]
    origin=tuple(min(p[k] for p in cert['pieces'][cert['anchor']]) for k in (0,1))
    if policy=='assemble':return out
    if policy=='deepest_piece':selected=[max(moving,key=lambda i:cert['depths'][i])]
    elif policy=='shallowest':selected=[min(moving,key=lambda i:cert['depths'][i])]
    elif policy=='largest_original':selected=[max(moving,key=lambda i:len(cert['pieces'][i]))]
    elif policy=='smallest_original':selected=[min(moving,key=lambda i:len(cert['pieces'][i]))]
    elif policy=='most_ports':selected=[max(moving,key=lambda i:sum(v==2 for v in cert['pieces'][i].values()))]
    elif policy=='last_input':selected=[moving[-1]]
    elif policy=='all_movers':selected=moving
    elif policy=='longest_path':
        depths=longest_depths(cert['graph'],cert['anchor'])
        selected=[max(moving,key=lambda i:depths[i])]
    elif policy=='euclidean':selected=[max(moving,key=lambda i:sum((min(p[k] for p in cert['pieces'][i])-origin[k])**2 for k in (0,1)))]
    else:raise ValueError('unknown prediction policy')
    for i in selected:
        for (r,c),v in cert['pieces'][i].items():
            if v!=2:out[r][c]=8
    return out

def longest_depths(graph,anchor):
    """Wrong-rule diagnostic: longest simple path, not BFS distance."""
    distances=[-1]*len(graph)
    def walk(node,seen,depth):
        distances[node]=max(distances[node],depth)
        for other in graph[node]:
            if other not in seen:walk(other,seen|{other},depth+1)
    walk(anchor,{anchor},0)
    return distances

# Rooted lattice paths, trees, and a six-cycle. Their leaves fold back toward the anchor, so graph
# depth is not Euclidean distance. Edges, not adjacent tile positions, join.
_LAYOUTS=(
    ([(0,0),(0,1),(1,1),(1,0)],[(0,1),(1,2),(2,3)]),
    ([(0,0),(0,1),(1,1),(2,1),(2,0),(-1,0)],[(0,1),(1,2),(2,3),(3,4),(0,5)]),
    ([(0,0),(-1,0),(-1,1),(0,1),(1,1)],[(0,1),(1,2),(2,3),(3,4)]),
    ([(0,0),(0,-1),(1,-1),(1,0),(1,1),(0,1)],[(0,1),(1,2),(2,3),(3,4),(4,5)]),
    ([(0,0),(0,1),(-1,1),(-1,2),(0,2),(1,2),(1,1)],[(0,1),(1,2),(2,3),(3,4),(4,5),(5,6)]),
    ([(0,0),(0,1),(-1,1),(-1,2),(0,2),(1,2),(1,1),(1,0)],[(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(0,7)]),
    ([(0,0),(0,1),(0,2),(1,2),(1,1),(1,0)],[(0,1),(1,2),(2,3),(3,4),(4,5),(5,0)]),
)

def _d4(grid,pose):
    result=deepcopy(grid)
    if pose>=4:result=[row[::-1] for row in result]
    for _ in range(pose%4):result=[list(row) for row in zip(*result[::-1])]
    return result

def _build_scene(seed,index,attempt):
    rng=random.Random(f'cbebaa4b:scene:{seed}:{index}:{attempt}')
    # The last source query is large and rich; presentation order is independent.
    layout_id=(index if index<2 else (index-2)%len(_LAYOUTS))
    if index==1:layout_id=6  # minimum lesson must distinguish shortest from longest paths
    if index==9:layout_id=5
    vertices,edges=_LAYOUTS[layout_id];n=len(vertices);side=5
    size=30 if index in (8,9) else rng.randint(27,30)
    origin=size-17;stride=6
    deepest=max(range(n),key=lambda k:_tree_depths(n,edges)[k])
    colors=[4]+[rng.choice([1,3,5,6,7,9]) for _ in range(n-1)]
    shapes=[]
    for i in range(n):
        # Outer frames and optional internal stripes remain connected. The
        # occupancy varies independently of graph depth; teaching checks below
        # reject both minimum- and maximum-area shortcuts.
        stripes=rng.sample([1,2,3],rng.randint(2 if index==8 else 0,3))
        body={(r,c):colors[i] for r in range(side) for c in range(side)
              if r in (0,side-1) or c in (0,side-1) or r in stripes}
        shapes.append(body)
    signatures=[(0,1),(0,2),(0,3),(0,4),(0,1,3),(0,1,4),(0,2,4),(0,2,3)]
    rng.shuffle(signatures)
    for (a,b),signature in zip(edges,signatures):
        delta=(vertices[b][0]-vertices[a][0],vertices[b][1]-vertices[a][1])
        offset=rng.randint(0,side-1-max(signature));sig=[x+offset for x in signature]
        if delta==(0,1):pa=[(x,side) for x in sig];pb=[(x,-1) for x in sig]
        elif delta==(0,-1):pa=[(x,-1) for x in sig];pb=[(x,side) for x in sig]
        elif delta==(1,0):pa=[(side,x) for x in sig];pb=[(-1,x) for x in sig]
        elif delta==(-1,0):pa=[(-1,x) for x in sig];pb=[(side,x) for x in sig]
        else:raise AssertionError('nonadjacent declared edge')
        shapes[a].update({p:2 for p in pa});shapes[b].update({p:2 for p in pb})
    positions=[(origin+r*stride,origin+c*stride) for r,c in vertices]
    expected=[[0]*size for _ in range(size)]
    for shape,(dr,dc) in zip(shapes,positions):
        for (r,c),v in shape.items():
            if not(0<=r+dr<size and 0<=c+dc<size):raise ValueError('scene outside bounds')
            if expected[r+dr][c+dc] not in (0,2) or (expected[r+dr][c+dc]==2 and v!=2):raise ValueError('body collision')
            expected[r+dr][c+dc]=v
    choices=[(r,c) for r in (1,origin,size-side-1) for c in (1,origin,size-side-1) if (r,c)!=(origin,origin)]
    rng.shuffle(choices);scattered=[(origin,origin)]+choices[:n-1]
    if index in (8,9):
        rows=[r for r,c in scattered];cols=[c for r,c in scattered]
        if min(rows)!=1 or max(rows)!=size-side-1 or min(cols)!=1 or max(cols)!=size-side-1:
            raise ValueError('stress scene must occupy both extremes on both axes')
    # No positional answer encoding: input slots are random, not graph order.
    grid=[[0]*size for _ in range(size)]
    for shape,(dr,dc) in zip(shapes,scattered):
        for (r,c),v in shape.items():
            if grid[r+dr][c+dc]:raise ValueError('scatter collision')
            grid[r+dr][c+dc]=v
    pose=rng.randrange(8);grid=_d4(grid,pose);expected=_d4(expected,pose)
    cert=solve(grid)
    if cert['output']!=expected:raise ValueError('constructive placement differs from inferred assembly')
    if cert['depths'].count(max(cert['depths']))!=1:raise ValueError('nonunique deepest piece')
    alt=deepcopy(expected);win=cert['depths'].index(max(cert['depths']))
    for (r,c),v in cert['pieces'][win].items():
        if v!=2:alt[r][c]=8
    return grid,expected,alt,{'layout':layout_id,'pose':pose,'depths':cert['depths'],
                            'search_nodes':cert['search_nodes'],'winner':win}

def _tree_depths(n,edges):
    dist=[-1]*n;dist[0]=0;todo=deque([0]);graph=[[] for _ in range(n)]
    for a,b in edges:graph[a].append(b);graph[b].append(a)
    while todo:
        a=todo.popleft()
        for b in graph[a]:
            if dist[b]<0:dist[b]=dist[a]+1;todo.append(b)
    return dist

@lru_cache(maxsize=128)
def _bank(seed):
    scenes=[]
    for i in range(10):
        for attempt in range(80):
            try:
                scene=_build_scene(seed,i,attempt)
                if i==0 and any(predict(scene[0],p)==scene[2] for p in BASE_RIVALS):
                    continue
                if i==1 and predict(scene[0],'longest_path')==scene[2]:continue
                if any(old[0]==scene[0] for old in scenes):continue
                scenes.append(scene);break
            except ValueError:
                continue
        else:raise ValueError(f'cannot construct unique scene {i} for seed {seed}')
    return scenes

def generate(seed,settings,demos=2,queries=4):
    policy=_settings(settings)
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('seed must be an exact integer in 0..2^63-1')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be an integer in 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be an integer in 1..4')
    scenes=_bank(seed);order=list(range(4));random.Random(f'cbebaa4b:presentation:{seed}').shuffle(order)
    def pair(s):return {'input':deepcopy(s[0]),'output':deepcopy(s[1 if policy=='assemble' else 2])}
    return {'train':[pair(s) for s in scenes[:demos]],
            'test':[pair(scenes[6+i]) for i in order[:queries]],
            'program_solution':program(settings),
            'private':{'seed':seed,'settings':dict(settings),'query_permutation':order,
                       'scene_certificates':deepcopy([s[3] for s in scenes])}}

def public_turn(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
    view={'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
          'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
    for pair in view['train']:_grid(pair['input']);_grid(pair['output'])
    _grid(view['test'][0]['input'])
    return view
