"""Color-keyed, component-wise settling; standalone copied-worker implementation.

Discover each uniform destination band and its edge-marker color. Split the
upper staging area into monochrome four-connected components, retain columns,
and translate each shape to its color's band floor or ceiling. Python labels
are claims, independently checked against reference.rkt by protected Racket.
"""
import random

RULE_TASK_ID = 'ee_7c66cb00'
TASK_ID = 'public_eval_7c66cb00'
VERSION = '1.0.0'
SETTINGS = ('floor', 'ceiling')


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid_check(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or
        type(g[0]) is not list or not 1 <= len(g[0]) <= 30 or
        any(type(row) is not list or len(row) != len(g[0]) or
            any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g)):
        raise ValueError('expected rectangular 1..30 grid of exact integer colors')


def components(g, background, connectivity=4):
    points={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=background}
    offsets=((-1,0),(1,0),(0,-1),(0,1))
    if connectivity==8:offsets+=((-1,-1),(-1,1),(1,-1),(1,1))
    result=[]
    while points:
        first=min(points);points.remove(first);color=g[first[0]][first[1]]
        queue=[first];seen=[first]
        while queue:
            r,c=queue.pop()
            for dr,dc in offsets:
                p=(r+dr,c+dc)
                if p in points and g[p[0]][p[1]]==color:
                    points.remove(p);queue.append(p);seen.append(p)
        result.append({'color':color,'cells':sorted(seen)})
    return result


def analyze(g):
    grid_check(g);h,w=len(g),len(g[0])
    if w<5:raise ValueError('canvas is too narrow for marked bands')
    bg=g[0][0]
    rows=[r for r,row in enumerate(g) if row[0]==row[-1] and row[0]!=row[1]
          and all(v==row[1] for v in row[1:-1])]
    if not rows or rows[0]<1:raise ValueError('staging area and marked bands required')
    bands=[]
    for r in rows:
        color,marker=g[r][1],g[r][0]
        if bands and bands[-1]['bottom']==r-1 and bands[-1]['color']==color and bands[-1]['marker']==marker:
            bands[-1]['bottom']=r
        else:bands.append({'top':r,'bottom':r,'color':color,'marker':marker})
    if len(bands)<2 or len({b['color'] for b in bands})!=len(bands):
        raise ValueError('need at least two distinct color-keyed bands')
    if any(b['color']==bg for b in bands):raise ValueError('band interior cannot be staging background')
    stage=rows[0];lookup={b['color']:b for b in bands}
    if any(any(v!=bg for v in g[r]) for r in range(stage,h) if r not in rows):
        raise ValueError('only uniform background separators allowed outside bands')
    if any(g[r][0]!=bg or g[r][-1]!=bg for r in range(stage)):
        raise ValueError('source objects must stay inside band marker columns')
    objs=components(g[:stage],bg)
    if not objs:raise ValueError('empty staging area')
    landing=set()
    for obj in objs:
        if obj['color'] not in lookup:raise ValueError('object has no matching band')
        band=lookup[obj['color']];rs=[r for r,c in obj['cells']]
        if max(rs)-min(rs)>band['bottom']-band['top']:raise ValueError('object taller than destination band')
        # Both requested settings must be collision-free on the admitted grammar.
        for mode in SETTINGS:
            delta=band['bottom']-max(rs) if mode=='floor' else band['top']-min(rs)
            for r,c in obj['cells']:
                key=(mode,r+delta,c)
                if key in landing:raise ValueError('settled components overlap')
                landing.add(key)
    return {'background':bg,'stage_end':stage,'bands':bands,'components':objs}


def render(g, info, mode='floor', *, objects=None, targets=None, recolor=True,
           erase=True, flatten=False, box=False, center=False):
    """Paint only after measuring component-to-band destinations."""
    out=[row[:] for row in g]
    if erase:
        for r in range(info['stage_end']):out[r]=[info['background']]*len(g[0])
    lookup={b['color']:b for b in info['bands']} if targets is None else targets
    for obj in info['components'] if objects is None else objects:
        cells=obj['cells'];rs=[r for r,c in cells];cs=[c for r,c in cells];b=lookup[obj['color']]
        delta=b['bottom']-max(rs) if mode=='floor' else b['top']-min(rs)
        if center:delta=b['top']+(b['bottom']-b['top']-(max(rs)-min(rs)))//2-min(rs)
        if box:cells=[(r,c) for r in range(min(rs),max(rs)+1) for c in range(min(cs),max(cs)+1)]
        for r,c in cells:
            rr=(b['bottom'] if mode=='floor' else b['top']) if flatten else r+delta
            if 0<=rr<len(g):out[rr][c]=b['marker'] if recolor else obj['color']
    return out


def solve(g, mode='floor'):
    if type(mode) is not str or mode not in SETTINGS:raise ValueError('unknown settling mode')
    return render(g,analyze(g),mode)


def rule_mirror(g):return solve(g)


def _construct(rng,h,w,n):
    bg=rng.randrange(10);fills=rng.sample([v for v in range(10) if v!=bg],n)
    markers=[rng.choice([v for v in range(10) if v!=color]) for color in fills]
    # At least one mapping points to another source color: simultaneous lookup
    # must not accidentally cascade through an earlier recoloring.
    markers[0]=fills[-1]
    heights=[rng.randint(4,5) for _ in range(n)]
    pad=rng.randrange(2);stage=h-sum(heights)-(n-1)-pad
    if stage<5:
        heights=[4]*n;stage=h-sum(heights)-(n-1)-pad
    order=list(range(n));rng.shuffle(order)
    g=[[bg]*w for _ in range(h)];row=stage
    for i in order:
        for r in range(row,row+heights[i]):g[r]=[markers[i]]+[fills[i]]*(w-2)+[markers[i]]
        row+=heights[i]+1
    # Composite ring: its center belongs to another destination band.
    y=rng.randrange(stage-2);x=1+rng.randrange(2)
    for r in range(3):
        for c in range(3):g[y+r][x+c]=fills[0] if r in (0,2) or c in (0,2) else fills[1]
    # A separate L and diagonal-only same-color singleton defeat grouping by
    # color or eight-connectivity; their settled column footprints are disjoint.
    y=rng.randrange(stage-2);x=(w-5)//2
    shape=[(0,0),(1,0),(2,0),(2,1),(2,2)]
    if rng.randrange(2):shape=[(2-r,c) for r,c in shape];singleton=(1,3)
    else:singleton=(1,3)
    for r,c in shape:g[y+r][x+c]=fills[0]
    g[y+singleton[0]][x+singleton[1]]=fills[0]
    # Third object varies shape/height and uses the last fill color.
    y=rng.randrange(stage-2);x=w-5
    shape=rng.choice([[(0,1),(1,0),(1,1),(1,2),(2,1)],
                      [(0,0),(0,1),(0,2),(1,0),(2,0)],
                      [(0,0),(0,1),(1,0),(1,1)]])
    for r,c in shape:g[y+r][x+c]=fills[-1]
    if rng.randrange(2):g=[row[::-1] for row in g]
    analyze(g)
    return g


def scene(seed,index,kind):
    integer(seed,0,2**63-1,'seed')
    if kind not in ('demo','query'):raise ValueError('unknown scene kind')
    integer(index,0,5 if kind=='demo' else 3,'index')
    dims=((21,19),(24,22),(22,24),(26,26),(25,28),(28,25)) if kind=='demo' else ((22,20),(25,23),(28,27),(30,30))
    h,w=dims[index];rng=random.Random(f'7c66cb00:v1:{seed}:{kind}:{index}')
    n=2 if kind=='demo' and index==0 else (3 if kind=='demo' and index==1 else rng.choice((2,3)))
    return _construct(rng,h,w,n)


def generate(seed=0,sample_index=0,difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**63-1,'sample_index')
    if difficulty is None:difficulty='medium'
    if difficulty not in ('easy','medium','hard','mixed'):raise ValueError('unsupported difficulty')
    rng=random.Random(f'7c66cb00:base:{seed}:{sample_index}:{difficulty}')
    if difficulty=='mixed':difficulty=rng.choice(('easy','medium','hard'))
    h,w,n={'easy':(21,19,2),'medium':(26,24,3),'hard':(30,30,3)}[difficulty]
    return _construct(rng,h,w,n)


def self_check(g,difficulty=None):
    try:analyze(g)
    except (ValueError,TypeError) as exc:return [str(exc)]
    return []
