"""Independent gate rewrite and endpoint-flow interpreter, without label lookup."""
DIRS=((-1,0),(1,0),(0,-1),(0,1))
RIVALS=('ignore_gate_topology','opposite_flow','one_per_component',
        'global_extreme','straight_drop','omit_pole_extension')


def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0])
               or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected rectangular 1..30 exact-integer grid')


def rewrite(g):
    grid_check(g)
    if any(v not in (0,3,7,8) for row in g for v in row):raise ValueError('Input palette is 0,3,7,8')
    h,w=len(g),len(g[0]);out=[[8 if v==3 else v for v in row] for row in g];gates=[]
    for r in range(h):
        c=0
        while c<w:
            if g[r][c]!=7:c+=1;continue
            end=c
            while end<w and g[r][end]==7:end+=1
            if end-c!=3 or not 0<r<h-1:raise ValueError('Gate must be an interior horizontal triple')
            middle=c+1
            if g[r-1][middle]!=8 or g[r+1][middle]!=8:raise ValueError('Gate pole requires clear cyan neighbors')
            gates.append((r,middle));out[r][c:end]=[8,6,8];out[r-1][middle]=out[r+1][middle]=6;c=end
    return out,gates


def analyze(g,*,routing='gates'):
    if routing not in ('gates','frozen'):raise ValueError('Unknown routing analysis')
    base,gates=rewrite(g);h,w=len(g),len(g[0])
    geometry=base if routing=='gates' else [[8 if v==3 else 0 if v==7 else v for v in row] for row in g]
    todo={(r,c) for r in range(h) for c in range(w) if geometry[r][c]==8};comps=[]
    while todo:
        start=min(todo);todo.remove(start);stack=[start];cells={start}
        while stack:
            r,c=stack.pop()
            for dr,dc in DIRS:
                p=(r+dr,c+dc)
                if p in todo:todo.remove(p);cells.add(p);stack.append(p)
        adjacency={p:sorted((p[0]+dr,p[1]+dc) for dr,dc in DIRS if (p[0]+dr,p[1]+dc) in cells) for p in cells}
        max_degree=max(map(len,adjacency.values()));ends=sorted(p for p,ns in adjacency.items() if len(ns)<=1)
        sources=sorted(p for p in cells if g[p[0]][p[1]]==3)
        if max_degree>2:raise ValueError('Admitted cyan walkways are nonbranching')
        if any(p not in ends for p in sources):raise ValueError('Green markers must start at path endpoints')
        comps.append({'cells':sorted(cells),'endpoints':ends,'sources':sources,'adjacency':adjacency,'max_degree':max_degree})
    return {'base':base,'gates':gates,'components':comps}


def ordered_path(component,start):
    path=[];previous=None;current=start
    while current is not None:
        path.append(current)
        ns=[p for p in component['adjacency'][current] if p!=previous]
        previous,current=current,ns[0] if ns else None
        if current==start:break
    return path


def destinations(component,flow):
    sources=component['sources'];ends=component['endpoints']
    if not sources:return []
    if not ends or ends[0][0]==ends[-1][0]:return sources[:]
    target=(max if flow=='down' else min)(ends,key=lambda p:p[0])
    return ordered_path(component,target)[:len(sources)]


def solve(g,flow='down',*,routing='gates'):
    if flow not in ('down','up'):raise ValueError('Undeclared flow')
    info=analyze(g,routing=routing);out=[row[:] for row in info['base']]
    for comp in info['components']:
        for r,c in destinations(comp,flow):out[r][c]=3
    return out


def rival(g,flow,name):
    if name not in RIVALS:raise ValueError('Unknown rival')
    if name=='ignore_gate_topology':return solve(g,flow,routing='frozen')
    if name=='opposite_flow':return solve(g,'up' if flow=='down' else 'down')
    if name=='omit_pole_extension':
        info=analyze(g);out=solve(g,flow)
        for r,c in info['gates']:out[r-1][c]=out[r+1][c]=8
        return out
    info=analyze(g);out=[row[:] for row in info['base']]
    if name=='global_extreme':
        n=sum(row.count(3) for row in g)
        cells=sorted((p for comp in info['components'] for p in comp['cells']),key=lambda p:((-p[0] if flow=='down' else p[0]),p[1]))
        for r,c in cells[:n]:out[r][c]=3
        return out
    for comp in info['components']:
        dest=destinations(comp,flow)
        if name=='one_per_component':dest=dest[:1]
        elif name=='straight_drop' and dest:
            row=(max if flow=='down' else min)(r for r,c in comp['cells'])
            dest=[(row,c) for r,c in comp['sources']]
        for r,c in dest:out[r][c]=3
    return out
