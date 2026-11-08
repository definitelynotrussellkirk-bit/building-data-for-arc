"""Varied marker-linked rectangular pockets; original-only branches stay explicit.

This constructor covers one clean connected indicator network, variable numbers
of selected and unselected rectangular enclosures, geometry, palettes and views.
Canonical contamination/irregular-enclosure branches are original-only evidence.
"""
from pathlib import Path
from collections import Counter
import copy
import random
BASE=Path(__file__).resolve().parent
MODES=('clean','all')

def _neighbors(g,r,c):
    for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
        if 0<=rr<len(g) and 0<=cc<len(g[0]):yield rr,cc

def analyze(g):
    freq=Counter(x for row in g for x in row);bg=freq.most_common(1)[0][0]
    marker=next(v for v,n in freq.items() if v!=bg and n==1)
    mp=next((r,c)for r,row in enumerate(g)for c,v in enumerate(row)if v==marker)
    indicator=next(g[r][c]for r,c in _neighbors(g,*mp)if g[r][c]not in (bg,marker))
    frame=next(v for v in freq if v not in (bg,marker,indicator))
    left={(r,c)for r,row in enumerate(g)for c,v in enumerate(row)if v==bg};pockets=[]
    while left:
        start=min(left);left.remove(start);stack=[start];cells=[];boundary=set()
        while stack:
            p=stack.pop();cells.append(p)
            for q in _neighbors(g,*p):
                if g[q[0]][q[1]]==bg:
                    if q in left:left.remove(q);stack.append(q)
                else:boundary.add(q)
        if boundary and all(g[r][c]==frame for r,c in boundary):
            selected=any(g[rr][cc]==indicator for r,c in boundary for rr,cc in _neighbors(g,r,c))
            pockets.append((cells,selected))
    return dict(background=bg,marker=marker,indicator=indicator,frame=frame,pockets=pockets)

def solve(g,mode):
    if mode not in MODES:raise ValueError('bad mode')
    d=analyze(g);out=copy.deepcopy(g)
    for cells,selected in d['pockets']:
        if mode=='all' or selected:
            for r,c in cells:out[r][c]=d['marker']
    return out

def _transform(g,turns,mirror):
    if mirror:g=[list(reversed(row))for row in g]
    for _ in range(turns):g=[list(row)for row in zip(*g[::-1])]
    return g

def scene(seed,index,route_offset=0):
    if type(seed)is not int or not 0<=seed<2**63 or type(index)is not int or index<0:raise ValueError('bad scene request')
    rng=random.Random(f'8b-pocket-v2:{seed}:{index}')
    h,w=((30,30)if index%4==0 else rng.choice([(18,22),(22,18),(24,28),(28,24),(26,30),(30,26)]))
    nr=rng.randint(2,min(4,h//6));nc=rng.randint(2,min(4,w//6))
    dense=(h,w)==(30,30)and index%8==0
    if dense:nr=nc=4
    bg,marker,indicator,frame=rng.sample(range(10),4)
    g=[[bg]*w for _ in range(h)];boxes=[]
    for br in range(nr):
        y0=br*h//nr;y1=(br+1)*h//nr
        for bc in range(nc):
            x0=bc*w//nc;x1=(bc+1)*w//nc
            bh=(y1-y0-2)if dense else rng.randint(3,y1-y0-2)
            bw=(x1-x0-2)if dense else rng.randint(3,x1-x0-2)
            r=y0+2;c=rng.randint(x0+1,x1-bw-1)
            for x in range(c,c+bw):g[r][x]=g[r+bh-1][x]=frame
            for y in range(r,r+bh):g[y][c]=g[y][c+bw-1]=frame
            boxes.append((br,bc,r,c,bh,bw))
    row=rng.randrange(nr);selected=set(rng.sample(range(nc),rng.randint(2 if index%8==0 else 1,nc)))
    row=(row+route_offset)%nr
    targets=[b for b in boxes if b[0]==row and b[1]in selected]
    lane=row*h//nr
    stems=[(r,c+rng.randint(1,bw-2))for br,bc,r,c,bh,bw in targets]
    g[lane][0]=marker
    for c in range(1,max(c for r,c in stems)+1):g[lane][c]=indicator
    for r,c in stems:
        for rr in range(lane+1,r):g[rr][c]=indicator
    view=random.Random(f'8b-view:{seed}:{index}')
    return _transform(g,view.randrange(4),view.choice([False,True]))

def _settings(settings):
    if type(settings)is not dict or set(settings)!={'indicator_policy'}or type(settings['indicator_policy'])is not str or settings['indicator_policy']not in MODES:raise ValueError('bad setting')

def program(settings):
    _settings(settings)
    return (BASE/('canonical.rkt'if settings['indicator_policy']=='clean'else'all_pockets.rkt')).read_text()

def generate(seed,settings,demos=2,queries=4):
    _settings(settings)
    if not(type(seed)is int and 0<=seed<2**63 and type(demos)is int and 2<=demos<=6 and type(queries)is int and 1<=queries<=4):raise ValueError('bad request')
    mode=settings['indicator_policy']
    trains=[scene(seed,i)for i in range(6)]
    query_ids=list(range(100,104));random.Random(f'8b-query-order:{seed}').shuffle(query_ids)
    tests=[scene(seed,i)for i in query_ids]
    pair=lambda g:dict(input=g,output=solve(g,mode))
    return dict(train=[pair(g)for g in trains[:demos]],test=[pair(g)for g in tests[:queries]],program_solution=program(settings))

def public_view(ep,index=0):
    if type(index)is not int or not 0<=index<len(ep['test']):raise ValueError('bad query index')
    return copy.deepcopy(dict(train=[dict(input=p['input'],output=p['output'])for p in ep['train']],test=[dict(input=ep['test'][index]['input'])]))
