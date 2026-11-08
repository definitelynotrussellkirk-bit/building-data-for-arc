"""Inward region-distance bands, inferred from sparse colored depth markers."""
from collections import Counter,deque
CARDINAL=((-1,0),(1,0),(0,-1),(0,1))
KING=tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c)


def validate_grid(g):
    if type(g) is not list or not g or len(g)>30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('grid dimensions must be 1..30')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(x) is not int or not 0<=x<=9 for x in row) for row in g):raise ValueError('rectangular integer-color grid required')


def mode(values):
    count=Counter(values)
    return min(count,key=lambda x:(-count[x],x))


def components(cells):
    todo=set(cells);out=[]
    while todo:
        start=min(todo);todo.remove(start);q=deque([start]);comp={start}
        while q:
            r,c=q.popleft()
            for dr,dc in CARDINAL:
                n=(r+dr,c+dc)
                if n in todo:todo.remove(n);comp.add(n);q.append(n)
        out.append(comp)
    return out


def depths(cells,metric='king'):
    """Inward square erosion: distance zero touches the region complement."""
    steps=KING if metric=='king' else CARDINAL
    boundary=[p for p in cells if any((p[0]+dr,p[1]+dc) not in cells for dr,dc in steps)]
    depth={p:0 for p in boundary};q=deque(boundary)
    while q:
        r,c=q.popleft()
        for dr,dc in steps:
            p=(r+dr,c+dc)
            if p in cells and p not in depth:depth[p]=depth[(r,c)]+1;q.append(p)
    return depth


def records(g,metric='king'):
    validate_grid(g);bg=mode(x for row in g for x in row)
    others=[x for row in g for x in row if x!=bg]
    if not others:raise ValueError('wall color is missing')
    wall=mode(others)
    cells={(r,c) for r,row in enumerate(g) for c,x in enumerate(row) if x!=wall}
    out=[]
    for comp in components(cells):
        ds=depths(comp,metric)
        marked=[(ds[p],g[p[0]][p[1]]) for p in sorted(comp) if g[p[0]][p[1]]!=bg]
        n=max((d for d,x in marked),default=-1)+1
        palette=[mode(x for dd,x in marked if dd==d) if any(dd==d for dd,x in marked) else bg for d in range(n)] or [bg]
        out.append({'cells':comp,'depth':ds,'palette':palette})
    return bg,wall,out


def color_index(depth,n,propagation):
    if propagation=='cyclic' or n<=1:return depth%n
    period=2*n-2;k=depth%period
    return k if k<n else period-k


def solve(g,propagation='cyclic',metric='king'):
    if propagation not in ('cyclic','bouncing'):raise ValueError('invalid propagation')
    _,wall,recs=records(g,metric)
    out=[row[:] for row in g]
    for rec in recs:
        palette=rec['palette']
        for (r,c),d in rec['depth'].items():out[r][c]=palette[color_index(d,len(palette),propagation)]
    return out
