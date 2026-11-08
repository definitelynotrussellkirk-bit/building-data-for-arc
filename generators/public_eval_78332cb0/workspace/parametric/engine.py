"""Border-contact chain assembly and cumulative foreground parity; pure standard library."""
from copy import deepcopy
import itertools
import random

ORDER_FAULTS=('input_order','reverse_chain','area_sort','color_sort','overlap','min_port','horizontal_only','vertical_only')
POLICIES=('canonical','prefix_parity',*ORDER_FAULTS,*('prefix/'+m for m in ORDER_FAULTS),
          'raw_prefix','own_parity','rank_parity','color_parity','bbox_parity','reverse_prefix')

def _grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30 or
        any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected rectangular 1..30 exact integer ARC grid')

def _spans(flags):
    spans=[];start=None
    for i,separator in enumerate([*flags,True]):
        if not separator and start is None:start=i
        if separator and start is not None:spans.append((start,i));start=None
    return spans

def edges(t,axis):
    if axis=='vertical':return tuple(i for i,v in enumerate(t[0]) if v!=7),tuple(i for i,v in enumerate(t[-1]) if v!=7)
    return tuple(i for i,row in enumerate(t) if row[0]!=7),tuple(i for i,row in enumerate(t) if row[-1]!=7)

def _chains(tiles,matching='exact'):
    solutions=[];n=len(tiles)
    for axis in ('vertical','horizontal'):
        ports=[edges(t,axis) for t in tiles]
        def match(a,b):
            if not a or not b:return False
            if matching=='overlap':return bool(set(a)&set(b))
            if matching=='min_port':return min(a)==min(b)
            return a==b
        def visit(path):
            out=ports[path[-1]][1]
            if len(path)==n:
                if not out:solutions.append((axis,path))
                return
            if not out:return
            for i in range(n):
                if i not in path and match(out,ports[i][0]):visit(path+[i])
        for i in range(n):
            if not ports[i][0]:visit([i])
    return solutions

def _area(t):return sum(v!=7 for row in t for v in row)

def parse(g):
    _grid(g);h,w=len(g),len(g[0]);rs=_spans([all(v==6 for v in row) for row in g]);cs=_spans([all(row[c]==6 for row in g) for c in range(w)])
    if not rs or not cs or rs[0][0]!=0 or rs[-1][1]!=h or cs[0][0]!=0 or cs[-1][1]!=w:raise ValueError('no outer divider frame allowed')
    if len({b-a for a,b in rs})!=1 or len({b-a for a,b in cs})!=1:raise ValueError('panels must have equal dimensions')
    gaps=[sp[i+1][0]-sp[i][1] for sp in (rs,cs) for i in range(len(sp)-1)]
    if not gaps or len(set(gaps))!=1:raise ValueError('uniform separator bands and at least two panels required')
    tiles=[[row[c0:c1] for row in g[r0:r1]] for r0,r1 in rs for c0,c1 in cs]
    if not 2<=len(tiles)<=6 or any(6 in row for t in tiles for row in t) or any(not _area(t) for t in tiles):raise ValueError('invalid panel grammar')
    solutions=_chains(tiles)
    if len(solutions)!=1:raise ValueError(f'unique complete border chain required; got {len(solutions)}')
    axis,order=solutions[0];th,tw=len(tiles[0]),len(tiles[0][0]);sep=gaps[0]
    oh,ow=(len(tiles)*(th+sep)-sep,tw) if axis=='vertical' else (th,len(tiles)*(tw+sep)-sep)
    if max(oh,ow)>30:raise ValueError('assembled output exceeds ARC bounds')
    return {'tiles':tiles,'axis':axis,'order':order,'separator':sep,'areas':[_area(t) for t in tiles],
            'panel_shape':[th,tw],'input_layout':[len(rs),len(cs)]}

def _pack(tiles,nrows,ncols,sep):
    th,tw=len(tiles[0]),len(tiles[0][0]);out=[]
    for i in range(nrows):
        for r in range(th):
            row=[]
            for j in range(ncols):
                row+=tiles[i*ncols+j][r]
                if j+1<ncols:row += [6]*sep
            out.append(row)
        if i+1<nrows:out.extend([[6]*len(out[0]) for _ in range(sep)])
    return out

def _bbox(t):
    pts=[(r,c) for r,row in enumerate(t) for c,v in enumerate(row) if v!=7]
    return (max(r for r,c in pts)-min(r for r,c in pts)+1)*(max(c for r,c in pts)-min(c for r,c in pts)+1)

def predict(g,mode='canonical'):
    if mode not in POLICIES:raise ValueError('unknown assembly policy')
    p=parse(g);tiles=p['tiles'];order=p['order'][:];axis=p['axis'];n=len(tiles);areas=p['areas'][:]
    paint=mode=='prefix_parity' or mode.startswith('prefix/') or mode in ('raw_prefix','own_parity','rank_parity','color_parity','bbox_parity','reverse_prefix')
    fault=mode.removeprefix('prefix/')
    if fault=='input_order':order=list(range(n))
    elif fault=='reverse_chain':order=order[::-1]
    elif fault=='area_sort':order=sorted(range(n),key=lambda i:(areas[i],i))
    elif fault=='color_sort':order=sorted(range(n),key=lambda i:(min(v for row in tiles[i] for v in row if v!=7),i))
    elif fault in ('overlap','min_port'):
        candidates=_chains(tiles,fault)
        if candidates:axis,order=candidates[0]
    elif fault in ('horizontal_only','vertical_only'):
        proposed=fault.split('_')[0];h,w=p['panel_shape'];length=n*((w if proposed=='horizontal' else h)+p['separator'])-p['separator']
        if length<=30:axis=proposed
    source_order=list(range(n)) if mode=='raw_prefix' else order[::-1] if mode=='reverse_prefix' else order
    if mode=='color_parity':areas=[len({v for row in t for v in row if v!=7}) for t in tiles]
    elif mode=='bbox_parity':areas=[_bbox(t) for t in tiles]
    prefix={};total=0
    for i in source_order:total+=areas[i];prefix[i]=total
    rendered=[]
    for rank,i in enumerate(order):
        value=areas[i] if mode=='own_parity' else rank+1 if mode=='rank_parity' else prefix[i]
        rendered.append([[8 if paint and value%2 and v!=7 else v for v in row] for row in tiles[i]])
    return _pack(rendered,n if axis=='vertical' else 1,1 if axis=='vertical' else n,p['separator'])

def _connected(cells):
    if not cells:return False
    todo=[next(iter(cells))];seen=set(todo)
    while todo:
        r,c=todo.pop()
        for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if p in cells and p not in seen:seen.add(p);todo.append(p)
    return seen==cells

def _panel(rng,height,width,entry,exit,color,parity):
    mid=height//2;columns=set(entry)|set(exit)
    cells={(mid,c) for c in range(min(columns),max(columns)+1)}
    for c in entry:cells.update((r,c) for r in range(mid+1))
    for c in exit:cells.update((r,c) for r in range(mid,height))
    candidates={(r,c) for r in range(1,height-1) for c in range(1,width-1)}
    for _ in range(rng.randrange(0,max(1,len(candidates)//2))):
        frontier=sorted(p for p in candidates-cells if any(q in cells for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1))))
        if frontier:cells.add(rng.choice(frontier))
    if len(cells)%2!=parity:
        frontier=sorted(p for p in candidates-cells if any(q in cells for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1))))
        if frontier:cells.add(rng.choice(frontier))
        else:
            removable=[p for p in sorted(cells&candidates) if _connected(cells-{p})]
            if not removable:raise ValueError('cannot realize requested connected-area parity')
            cells.remove(rng.choice(removable))
    t=[[7]*width for _ in range(height)]
    for r,c in cells:t[r][c]=color
    return t

def _scene(seed,index):
    rng=random.Random(f'78332cb0:scene:{seed}:{index}')
    if index==0:n,th,tw,sep,axis=4,5,5,1,'vertical';keys=[(1,),(1,2),(1,3)];parities=[1,0,0,1]
    elif index==1:n,th,tw,sep,axis=3,5,5,1,'horizontal';keys=[(1,3),(2,)];parities=[0,1,1]
    elif index==6:n,th,tw,sep,axis=2,3,4,1,rng.choice(['vertical','horizontal']);keys=[(1,)];parities=[1,0]
    elif index==9:n,th,tw,sep,axis=4,6,30,2,rng.choice(['vertical','horizontal']);keys=[(2,12,26),(4,18),(9,24)];parities=[1,0,1,0]
    else:
        n=rng.choice([3,4,5]);th,tw=5,rng.choice([5,6]);sep=1;axis=rng.choice(['vertical','horizontal'])
        signatures=[x for size in range(1,3) for x in itertools.combinations(range(1,tw-1),size)]
        keys=rng.sample(signatures,n-1);parities=[rng.randrange(2) for _ in range(n)]
    colors=rng.sample([0,1,2,3,4,5,9],n)
    if index==0 and (colors==sorted(colors) or colors==sorted(colors,reverse=True)):
        colors[0],colors[1]=colors[1],colors[0]
    if index==8:colors=[colors[0]]*n
    elif index==7:colors[-1]=colors[0]
    tiles=[_panel(rng,th,tw,() if i==0 else keys[i-1],() if i==n-1 else keys[i],colors[i],parities[i]) for i in range(n)]
    if axis=='horizontal':tiles=[[list(row) for row in zip(*t)] for t in tiles]
    h,w=len(tiles[0]),len(tiles[0][0])
    layouts=[(r,n//r) for r in range(1,n+1) if n%r==0 and r*(h+sep)-sep<=30 and (n//r)*(w+sep)-sep<=30]
    if index==0:layout=(2,2)
    elif index==1:layout=(3,1)
    else:layout=rng.choice(layouts)
    for attempt in range(100):
        permutation=list(range(n));rng.shuffle(permutation)
        if index==0 and permutation.index(2)>permutation.index(1):continue
        if permutation==list(range(n)) or (n>2 and permutation==list(reversed(range(n)))):continue
        g=_pack([tiles[i] for i in permutation],*layout,sep)
        cert=parse(g)
        if index in (0,9) and predict(g,'prefix_parity')==predict(g,'raw_prefix'):continue
        return g,{'profile':'thick_30' if index==9 else 'multiport' if index==0 else 'minimal' if index==6 else 'mixed',
                  'source_index':index,'axis':axis,'input_layout':list(layout),'chain':cert['order'],'areas':cert['areas'],'separator':sep}
    raise ValueError('bounded presentation construction exhausted')

def bank(seed):return [_scene(seed,i) for i in range(10)]
