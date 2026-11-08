"""Five-cell plus detection and overlap-cluster selection.

Self-contained so the ordinary runtime may stage this file without sidecars.
The native resource engine.py is byte-identical; a regression guards the copy.
Python labels are claims: the Racket reference is independently executed.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx

GENERATOR_ID = 'public_eval_1818057f'
TASK_ID = GENERATOR_ID
RULE_TASK_ID = 'ee_1818057f'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
SUMMARY = 'Recolor complete yellow pluses cyan; optionally select maximum overlap clusters.'
SETTINGS = ('all', 'largest_overlap')
AXES = {}
INVARIANTS = ['rectangular 1..30 integer-color grids', 'complete plus detection uses the original input', 'sampler has multiple unequal overlap clusters']
OFFSETS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
def integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value

def validate_grid(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
        or not 1 <= len(g[0]) <= 30 or any(type(row) is not list or len(row)!=len(g[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected a rectangular 1..30 integer-color grid')
    return g

def centers(g):
    validate_grid(g)
    return [(r,c) for r in range(1,len(g)-1) for c in range(1,len(g[0])-1)
            if all(g[r+dr][c+dc]==4 for dr,dc in OFFSETS)]

def clusters(points):
    """Plus footprints intersect exactly when center Manhattan distance <= 2."""
    todo=set(points);groups=[]
    while todo:
        first=min(todo);todo.remove(first);seen={first};stack=[first]
        while stack:
            r,c=stack.pop()
            near={p for p in todo if abs(p[0]-r)+abs(p[1]-c)<=2}
            todo-=near;seen|=near;stack.extend(sorted(near))
        groups.append(sorted(seen))
    return groups

def footprint(points):
    return {(r+dr,c+dc) for r,c in points for dr,dc in OFFSETS}

def chosen_centers(g, setting='all'):
    if setting not in SETTINGS:raise ValueError('unknown selection')
    pts=centers(g)
    if setting=='all' or not pts:return pts
    groups=clusters(pts);maximum=max(map(len,groups))
    return sorted(p for group in groups if len(group)==maximum for p in group)

def paint(g, points, only_centers=False):
    out=[row[:] for row in g]
    for r,c in (points if only_centers else footprint(points)):out[r][c]=8
    return out

def solve(g, setting='all'):
    return paint(g,chosen_centers(g,setting))

def _tile(n, height, width, rng, shape_hint=None):
    t=[[2]*width for _ in range(height)]
    if n==1:points={(1,1)}
    elif shape_hint=='cycle':points={(1,1),(1,3),(3,1),(3,3)}
    elif shape_hint=='path':points={(1,1),(1,3),(1,5),(3,5)}
    else:
        points={(1,1)}
        while len(points)<n:
            frontier=sorted({(r+dr,c+dc) for r,c in points for dr,dc in ((-2,0),(2,0),(0,-2),(0,2))
                             if 1<=r+dr<=5 and 1<=c+dc<=5}-points)
            points.add(rng.choice(frontier))
    for r,c in points:
        for dr,dc in OFFSETS:t[r+dr][c+dc]=4
    # A diagonal extra is irrelevant to a plus and must not disqualify it.
    t[0][0]=4
    if n==1:
        # A very large yellow component with just one plus. Joining at the
        # left edge cannot create another complete plus at the bar junction.
        for r in range(1,height):t[r][0]=4
        for r in range(height-2,height):
            for c in range(width):t[r][c]=4
    elif height>=10:
        # Dense non-plus distractor, separated from the matching stencil.
        color=rng.choice((0,1,3,4,5,6,7,9))
        for r in range(height-2,height):
            for c in range(width):t[r][c]=color
    if rng.randrange(2):t=t[::-1]
    if rng.randrange(2):t=[row[::-1] for row in t]
    return t

def scene(seed, index, kind='query'):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    if kind not in ('demo','query'):raise ValueError('kind must be demo or query')
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=GENERATOR_ID+':'+kind)
    rng=ctx.draw_rng('layout')
    if kind=='demo':
        sizes=((18,20),(19,21),(20,22),(21,23),(22,24),(23,25))
        h,w=sizes[index%6]
        counts=([4,3,1,2] if index%2==0 else [4,4,2,1])
    else:
        h,w=((17,19),(21,24),(26,27),(30,30))[index%4]
        counts=([3,2,1,2],[4,1,3,2],[5,3,5,1],[6,4,2,1])[index%4]
    # Winner position changes through the curriculum. The shift is public
    # geometry, independent of the private rule setting.
    rotation=(seed%4 + index)%4
    counts=counts[rotation:]+counts[:rotation]
    split_r=(h-1)//2;split_c=(w-1)//2
    specs=((0,0,split_r,split_c),(0,split_c+1,split_r,w-split_c-1),
           (split_r+1,0,h-split_r-1,split_c),(split_r+1,split_c+1,h-split_r-1,w-split_c-1))
    g=[[2]*w for _ in range(h)]
    four_seen=0
    for n,(r0,c0,th,tw) in zip(counts,specs):
        hint=None
        if kind=='demo' and index%2==1 and n==4:
            hint='cycle' if four_seen==0 else 'path';four_seen+=1
        tile=_tile(n,th,tw,rng,hint)
        for r,row in enumerate(tile):g[r0+r][c0:c0+tw]=row
    return g

def generate(seed, sample_index=0, difficulty=None, **overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('invalid difficulty')
    if overrides:raise ValueError('this bounded sampler declares no override axes')
    return scene(seed,sample_index,'query')

def self_check(g):
    try:
        pts=centers(g);groups=clusters(pts)
        if len(groups)<2 or len({len(s) for s in groups})<2:
            return ['requires multiple unequal plus-overlap groups']
        return []
    except (ValueError,TypeError,IndexError) as e:return [str(e)]

def rivals(g, setting):
    pts=centers(g);groups=clusters(pts);selected=chosen_centers(g,setting)
    if not pts:return {'identity':[r[:] for r in g]}
    isolated=[p for p in pts if all(g[p[0]+dr][p[1]+dc]!=4 for dr,dc in ((-1,-1),(-1,1),(1,-1),(1,1)))]
    # Label entire yellow components that contain any selected center.
    todo={(r,c) for r,row in enumerate(g) for c,x in enumerate(row) if x==4};components=[]
    while todo:
        p=min(todo);todo.remove(p);comp={p};stack=[p]
        while stack:
            r,c=stack.pop()
            q={(r+dr,c+dc) for dr,dc in OFFSETS[1:]}&todo
            todo-=q;comp|=q;stack.extend(q)
        components.append(comp)
    recolored=set().union(*(s for s in components if set(selected)&s))
    out=[row[:] for row in g]
    for r,c in recolored:out[r][c]=8
    max_area=max(map(len,components))
    area_pts=[p for p in pts if any(p in s and len(s)==max_area for s in components)]
    largest=sorted(groups,key=lambda s:(-len(s),s[0]))[0]
    return {
        'identity':[row[:] for row in g], 'all_pluses':solve(g,'all'),
        'largest_overlap':solve(g,'largest_overlap'), 'centers_only':paint(g,selected,True),
        'first_cluster':paint(g,groups[0]), 'last_cluster':paint(g,groups[-1]),
        'smallest_cluster':paint(g,[p for s in groups if len(s)==min(map(len,groups)) for p in s]),
        'isolated_diagonal_corners':paint(g,isolated), 'largest_yellow_component':paint(g,area_pts),
        'whole_yellow_components':out, 'first_maximum_only':paint(g,largest),
        'largest_union_area':paint(g,[p for s in groups if len(footprint(s))==max(len(footprint(t)) for t in groups) for p in s]),
    }
