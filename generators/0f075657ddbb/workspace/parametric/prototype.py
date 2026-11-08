"""Frame-band activation followed by cross-object area matching.

Python labels are claims. The native worker and audit execute independent Racket.
The admitted grammar uses nested complete yellow frames, one magenta key per
band, and distinct-area remote blue objects. Production generation is untouched.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
MODES=('fill_only','key_relay')
DIRS=((-1,0),(1,0),(0,-1),(0,1))

def components(g, color):
    todo={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==color}
    out=[]
    while todo:
        start=min(todo);todo.remove(start);pending=[start];cells={start}
        while pending:
            r,c=pending.pop()
            for dr,dc in DIRS:
                q=r+dr,c+dc
                if q in todo:todo.remove(q);cells.add(q);pending.append(q)
        out.append(sorted(cells))
    return out

def boxes(g):
    result=[]
    for cells in components(g,4):
        a,b=min(r for r,c in cells),min(c for r,c in cells)
        c,d=max(r for r,c in cells),max(c for r,c in cells)
        perimeter={(r,k) for r in range(a,c+1) for k in range(b,d+1)
                   if r in (a,c) or k in (b,d)}
        if a<c and b<d and set(cells)==perimeter:result.append((a,b,c,d))
    return sorted(result,key=lambda b:(-(b[2]-b[0]+1)*(b[3]-b[1]+1),b[0],b[1]))

def canonical(g):
    out=copy.deepcopy(g);bs=boxes(g);k=g[0].count(2)
    if not 1<=k<=len(bs):return out
    a,b,c,d=bs[k-1];inner=bs[k] if k<len(bs) else None
    for r in range(a+1,c):
        for col in range(b+1,d):
            if inner and inner[0]<r<inner[2] and inner[1]<col<inner[3]:continue
            if g[r][col]==0:out[r][col]=8
    return out

def active_keys(g,out):
    h,w=len(g),len(g[0])
    return [obj for obj in components(g,6) if any(
        0<=r+dr<h and 0<=c+dc<w and g[r+dr][c+dc]==0 and out[r+dr][c+dc]==8
        for r,c in obj for dr,dc in DIRS)]

def intermediate(g):
    stage=canonical(g);keys=active_keys(g,stage)
    return {'selector':g[0].count(2),'key_cells':keys[0] if len(keys)==1 else [],
            'key_size':len(keys[0]) if len(keys)==1 else None,
            'receiver_sizes':[len(x) for x in components(g,1)]}

def predict(g,mode):
    if mode not in MODES:raise ValueError('Unknown relay policy')
    out=canonical(g)
    if mode=='fill_only':return out
    keys=active_keys(g,out)
    if len(keys)!=1:return out
    receivers=[x for x in components(g,1) if len(x)==len(keys[0])]
    if len(receivers)==1:
        for r,c in receivers[0]:out[r][c]=3
    return out

def mode_of(settings):
    if type(settings) is not dict or set(settings)!={'relay_policy'} or settings['relay_policy'] not in MODES:
        raise ValueError('Exactly relay_policy=fill_only|key_relay is required')
    return settings['relay_policy']

def program(settings):
    return HERE.joinpath('canonical.rkt' if mode_of(settings)=='fill_only' else 'alternate.rkt').read_text()

def _rng(seed,label):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{label}'.encode()).digest(),'big'))

def _scene(seed,index):
    rng=_rng(seed,f'geometry:{index}')
    stress=index==9
    n=2 if index in (2,6) else 3
    h=30 if stress else 22+(index%5)
    w=30 if stress else rng.randint(26,29)
    g=[[0]*w for _ in range(h)]
    # Every band has positive room around its key, including the innermost.
    frames=[(2+2*i,2*i,h-1-2*i,w-11-2*i) for i in range(n)]
    for a,b,c,d in frames:
        for r in range(a,c+1):
            for col in range(b,d+1):
                if r in (a,c) or col in (b,d):g[r][col]=4
    sizes=[2,4,6][:n]
    if index==0:sizes=[4,2,6]
    elif index==1:sizes=[6,4,2]
    else:rng.shuffle(sizes)
    for (a,b,c,d),size in zip(frames,sizes):
        start=rng.randint(b+1,d-size)
        for col in range(start,start+size):g[a+1][col]=6
    k=(1 if index==0 else n if index==1 else
       0 if index==4 else n+1 if index==5 else rng.randint(1,n))
    header=rng.sample(list(range(w)),k)
    # Header locations vary; no leading-prefix shortcut.
    if k and header==list(range(k)):header=list(range(w-k,w))
    for col in header:g[0][col]=2
    # Two protected off-row reds, neither changing the row-0 selector.
    g[h-3][1]=2;g[h-4][1]=2
    # Preexisting cyan is not a new activation event.
    g[h-5][1]=8
    areas=[2,3,4,6,7]
    rng.shuffle(areas)
    # Local serpentine polyominoes vary their bboxes independently of area.
    for j,size in enumerate(areas):
        row=2+j*4
        width=(size if (j+index)%3==0 else (2 if size<=4 else 3))
        # Stress includes a right-edge receiver, not empty padding.
        col=w-width if j==4 else w-8+rng.randint(0,8-width)
        if size in (4,6):
            # Nonrectangular receivers force actual occupied-area measurement.
            # A six-cell shape's bounding box has area 9, not 6.
            path=([(0,0),(1,0),(1,1),(2,1)] if size==4 else
                  [(0,0),(1,0),(1,1),(2,1),(2,2),(1,2)])
            width=2 if size==4 else 3
            col=w-width if j==4 else w-8+rng.randint(0,8-width)
        else:
            path=[]
            for rr in range(3):
                cols=range(width) if rr%2==0 else range(width-1,-1,-1)
                path.extend((rr,cc) for cc in cols)
        for rr,cc in path[:size]:g[row+rr][col+cc]=1
    return g

def generate(seed,settings,demos,queries):
    mode=mode_of(settings)
    if type(seed) is not int:raise ValueError('seed must be an integer')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    train=[_scene(seed,i) for i in range(6)]
    bank=[_scene(seed,i) for i in range(6,10)]
    order=list(range(4));_rng(seed,'presentation').shuffle(order)
    bank=[bank[i] for i in order]
    inputs=train[:demos]+bank[:queries]
    if len({json.dumps(g) for g in inputs})!=len(inputs):raise ValueError('Duplicate inputs')
    def pair(g):return {'input':g,'output':predict(g,mode)}
    return {'train':[pair(g) for g in train[:demos]],'test':[pair(g) for g in bank[:queries]],
            'program_solution':program(settings)}

def public_view(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('Invalid query index')
    return copy.deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                          'test':[{'input':episode['test'][index]['input']}]})
