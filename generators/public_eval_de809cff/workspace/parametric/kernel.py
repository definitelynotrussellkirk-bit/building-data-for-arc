"""Noisy overlapping rectangles; self-contained production sampler and oracle.

Inputs contain two nonzero/noncyan rectangle colors, sparse zero holes, and
single-cell color noise. Long straight runs recover rectangle bounds. Majority
votes in pairwise overlaps recover an acyclic paint order. Python labels are
claims; reference.rkt and protected Racket are the independent authority.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import random

GENERATOR_ID = 'public_eval_de809cff'
TASK_ID = GENERATOR_ID
RULE_TASK_ID = 'ee_de809cff'
VERSION = '1.0.0'
SUMMARY = 'Restore overlapping rectangles, erase noise, and surround missing cells with the other color.'
EXAMPLES_NEEDED = 2
INVARIANTS = ['two rectangle colors excluding 0 and 8', 'straight visible runs of at least three cells identify bounds', 'acyclic majority overlap order', 'zero holes retain the original region identity']
AXES = {'grid_h': {'type':'int','valid':'18..30','default':'18..30'},
        'grid_w': {'type':'int','valid':'18..30','default':'18..30'}}


def integer(v, name, low=0, high=2**63-1):
    if type(v) is not int or not low <= v <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return v


def check_grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('grid dimensions must be 1..30')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('rectangular exact integer grid required')


def components(cells, diagonal=False):
    remaining=set(cells); answer=[]
    deltas=[(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1)
            if (dr or dc) and (diagonal or abs(dr)+abs(dc)==1)]
    while remaining:
        start=min(remaining);remaining.remove(start);todo=[start];part=[]
        while todo:
            r,c=todo.pop();part.append((r,c))
            for dr,dc in deltas:
                nxt=(r+dr,c+dc)
                if nxt in remaining:remaining.remove(nxt);todo.append(nxt)
        answer.append(sorted(part))
    return answer


def reconstruct(g):
    """Return restored grid and layer/edge records, without consulting outputs."""
    check_grid(g)
    colors=sorted(set(v for row in g for v in row)-{0})
    if len(colors)!=2 or 8 in colors:
        raise ValueError('expected exactly two nonzero/noncyan rectangle colors')
    regions=[]
    for color in colors:
        for comp in components((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==color):
            if len(comp)<9:continue
            cells=set(comp)
            rs=sorted({r for r,c in cells if (r,c+1) in cells and (r,c+2) in cells})
            cs=sorted({c for r,c in cells if (r+1,c) in cells and (r+2,c) in cells})
            if rs and cs:regions.append((color,min(rs),min(cs),max(rs),max(cs)))
    if len(regions)<2:raise ValueError('at least two recoverable rectangles required')
    edges=[]
    for i,(a,r,c,s,t) in enumerate(regions):
        for j,(b,u,v,w,x) in enumerate(regions):
            if i>=j or a==b:continue
            counts=Counter(g[y][z] for y in range(max(r,u),min(s,w)+1) for z in range(max(c,v),min(t,x)+1))
            if counts[a]!=counts[b]:edges.append((i,j) if counts[b]>counts[a] else (j,i))
            elif counts[a]:raise ValueError('ambiguous rectangle overlap')
    order=[]
    while len(order)<len(regions):
        ready=[i for i in range(len(regions)) if i not in order and all(u in order for u,v in edges if v==i)]
        if not ready:raise ValueError('cyclic rectangle occlusion')
        order.append(ready[0])
    out=[[0]*len(g[0]) for _ in g]
    for i in order:
        color,r,c,s,t=regions[i]
        for y in range(r,s+1):
            for x in range(c,t+1):out[y][x]=color
    return out, dict(regions=regions,edges=edges,paint_order=order)


def hole_records(g, restored):
    return [(r,c,restored[r][c]) for r,row in enumerate(g) for c,v in enumerate(row) if v==0 and restored[r][c]!=0]


def select_holes(holes, scope):
    if scope=='all':return list(holes)
    if scope!='largest_cluster':raise ValueError('unknown hole scope')
    groups=components((r,c) for r,c,k in holes)
    biggest=max(map(len,groups),default=0)
    selected={p for cc in groups if len(cc)==biggest for p in cc}
    return [hole for hole in holes if hole[:2] in selected]


def render(restored, holes, *, same_color=False, orthogonal=False, centers_only=False):
    out=[row[:] for row in restored];h=len(out);w=len(out[0])
    colors=sorted(set(v for row in restored for v in row)-{0})
    if not centers_only:
        for r,c,k in holes:
            other=k if same_color else next(v for v in colors if v!=k)
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if orthogonal and abs(dr)+abs(dc)>1:continue
                    if 0<=r+dr<h and 0<=c+dc<w:out[r+dr][c+dc]=other
    # All centers last; nearby halos may not erase a center.
    for r,c,k in holes:out[r][c]=8
    return out


def solve(g, scope='all'):
    restored,_=reconstruct(g)
    return render(restored,select_holes(hole_records(g,restored),scope))


def _transform(g, code):
    a=[row[:] for row in g]
    if code&4:a=[list(row) for row in zip(*a)]
    if code&2:a=a[::-1]
    if code&1:a=[row[::-1] for row in a]
    return a


def _draw(seed,index,h,w):
    rng=random.Random(int.from_bytes(hashlib.sha256(f'{VERSION}:{seed}:{index}'.encode()).digest(),'big'))
    a,b=rng.sample([1,2,3,4,5,6,7,9],2)
    top=rng.choice([0,1]);left=rng.choice([0,1]);cut=h//3+rng.choice([-1,0,1])
    layers=[(a,top,left,h//2,w*3//5),(b,cut,w//3,h-1-rng.randrange(2),w-1)]
    if index%3!=1:layers.append((a,h*2//3,0,h-1,w//2))
    base=[[0]*w for _ in range(h)]
    for k,r,c,s,t in layers:
        for y in range(r,s+1):
            for x in range(c,t+1):base[y][x]=k
    g=[row[:] for row in base]
    # Unequal, and sometimes tied, connected hole sizes. Every scene contains
    # several clusters: canonical/all and maximum-cluster labels must differ.
    sizes=([1,2,2,1],[2,3,1,2],[1,3,2,1,1],[2,4,1,2,1],[1,2,3,1],[3,1,3,2])[index%6]
    used=set()
    for number,size in enumerate(sizes):
        candidates=[]
        for r in range(h):
            for c in range(w):
                # Include boundary holes and non-straight cluster shapes.
                patterns=[[(0,i) for i in range(size)],[(i,0) for i in range(size)]]
                if size>=3:patterns.append([(0,0),(0,1)]+[(i,0) for i in range(1,size-1)])
                for pattern in patterns:
                    ps=[(r+dr,c+dc) for dr,dc in pattern]
                    if all(0<=y<h and 0<=x<w and base[y][x]==base[r][c]!=0 for y,x in ps):
                        if number==1 and index%2==0:
                            separated=all(abs(y-u)+abs(x-v)>1 for y,x in ps for u,v in used)
                            touches=any(max(abs(y-u),abs(x-v))==1 for y,x in ps for u,v in used)
                            if separated and touches:candidates.append(ps)
                        elif all(max(abs(y-u),abs(x-v))>1 for y,x in ps for u,v in used):candidates.append(ps)
        rng.shuffle(candidates)
        if number==1 and index%2==1:
            # The largest cluster, not merely a discarded singleton, teaches
            # that holes and halos may reach the canvas boundary.
            candidates=[ps for ps in candidates if any(y in (0,h-1) or x in (0,w-1) for y,x in ps)]
        # Some schedules deliberately put a hole on an inferred boundary.
        if number==0 and index%2==0:
            candidates.sort(key=lambda ps: not any(y==0 or x==0 or y==h-1 or x==w-1 or any(0<=y+dy<h and 0<=x+dx<w and base[y+dy][x+dx]!=base[y][x] for dy,dx in ((1,0),(-1,0),(0,1),(0,-1))) for y,x in ps))
        for ps in candidates[:200]:
            trial=[row[:] for row in g]
            for y,x in ps:trial[y][x]=0
            try:recovered,_=reconstruct(trial)
            except ValueError:continue
            if recovered==base:
                g=trial;used.update(ps);break
        else:raise ValueError('bounded lawful hole placement exhausted')
    # Sparse additions, protrusions and wrong-color defects are NOT zero holes.
    places=[(r,c) for r in range(h) for c in range(w) if (r,c) not in used]
    rng.shuffle(places);accepted=0
    for r,c in places:
        if any(max(abs(r-u),abs(c-v))<=2 for u,v in used):continue
        trial=[row[:] for row in g]
        trial[r][c]=rng.choice([a,b]) if base[r][c]==0 else (b if base[r][c]==a else a)
        if trial==g:continue
        try:recovered,_=reconstruct(trial)
        except ValueError:continue
        if recovered==base:g=trial;accepted+=1
        if accepted==3:break
    # Rectangles, overlap direction, holes, and canvas orientation all vary.
    code=rng.randrange(8)
    g=_transform(g,code)
    expected=_transform(base,code)
    actual,_=reconstruct(g)
    if actual!=expected:raise ValueError('transformed layer recovery failed')
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    integer(seed,'seed');integer(sample_index,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('unknown axes')
    dimrng=random.Random(int.from_bytes(hashlib.sha256(f'dim:{seed}:{sample_index}'.encode()).digest(),'big'))
    h=overrides.get('grid_h',dimrng.randrange(18,31));w=overrides.get('grid_w',dimrng.randrange(18,31))
    integer(h,'grid_h',18,30);integer(w,'grid_w',18,30)
    # Dimension overrides describe the final grid, including transposition.
    g=_draw(seed,sample_index,h,w)
    if (len(g),len(g[0]))!=(h,w):g=[list(row) for row in zip(*g)]
    return g


def self_check(grid, *, difficulty=None, meta=None):
    try:
        restored,info=reconstruct(grid)
        holes=hole_records(grid,restored)
        if not holes:return ['no missing cells']
        if not 2<=len(info['regions'])<=4:return ['unsupported number of rectangle layers']
        return []
    except (ValueError,TypeError,IndexError) as error:return [str(error)]
