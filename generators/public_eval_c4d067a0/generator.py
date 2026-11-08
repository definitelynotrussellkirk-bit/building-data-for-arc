"""Infer miniature-to-enlarged lattice registration; no corpus lookups."""
from __future__ import annotations
from collections import Counter


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}, not bool/coercible')
    return value


def check_grid(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('grid dimensions must be 1..30')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('rectangular exact integer colors required')


def components(g, bg):
    todo={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg}
    out=[]
    while todo:
        first=min(todo);todo.remove(first);color=g[first[0]][first[1]]
        stack=[first];cells=[first]
        while stack:
            r,c=stack.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in todo and g[p[0]][p[1]]==color:
                    todo.remove(p);cells.append(p);stack.append(p)
        out.append({'cells':sorted(cells),'color':color,
                    'bbox':(min(r for r,c in cells),min(c for r,c in cells),
                            max(r for r,c in cells),max(c for r,c in cells))})
    return out


def extract(g):
    check_grid(g)
    counts=Counter(v for row in g for v in row);bg,n=counts.most_common(1)[0]
    if list(counts.values()).count(n)!=1:raise ValueError('background must be uniquely modal')
    objects=components(g,bg)
    dots=[o for o in objects if len(o['cells'])==1]
    blocks=[o for o in objects if len(o['cells'])>1]
    if len(dots)<3 or len(blocks)<2:raise ValueError('at least three template dots and two seed squares required')
    side=blocks[0]['bbox'][2]-blocks[0]['bbox'][0]+1
    if side<2 or any((o['bbox'][2]-o['bbox'][0]+1!=side or o['bbox'][3]-o['bbox'][1]+1!=side or len(o['cells'])!=side*side) for o in blocks):
        raise ValueError('all seeds must be equal solid squares of side >=2')
    rr=sorted({o['bbox'][0] for o in dots});cc=sorted({o['bbox'][1] for o in dots})
    diffs=[b-a for xs in (rr,cc) for a,b in zip(xs,xs[1:])]
    if not diffs:raise ValueError('nontrivial template lattice required')
    spacing=min(diffs)
    if spacing<2 or any((r-rr[0])%spacing for r in rr) or any((c-cc[0])%spacing for c in cc):
        raise ValueError('template dots must lie on a separated uniform lattice')
    nr,nc=(rr[-1]-rr[0])//spacing+1,(cc[-1]-cc[0])//spacing+1
    pattern=[[bg]*nc for _ in range(nr)]
    for o in dots:
        r,c=o['cells'][0];pattern[(r-rr[0])//spacing][(c-cc[0])//spacing]=o['color']
    return dict(bg=bg,pattern=pattern,template_spacing=spacing,small_bbox=[rr[0],cc[0],rr[-1],cc[-1]],
                blocks=blocks,block_size=side,height=len(g),width=len(g[0]))


def registrations(data):
    pattern=data['pattern'];nr,nc=len(pattern),len(pattern[0]);side=data['block_size']
    first=data['blocks'][0];sr,sc=first['bbox'][:2]
    tr,tc,br,bc=data['small_bbox'];candidates=[]
    for pitch in range(side+1,max(data['height'],data['width'])+1):
        for pr,row in enumerate(pattern):
            for pc,color in enumerate(row):
                if color!=first['color']:continue
                ar,ac=sr-pr*pitch,sc-pc*pitch
                endr,endc=ar+(nr-1)*pitch+side,ac+(nc-1)*pitch+side
                if not (ar>=0 and ac>=0 and endr<=data['height'] and endc<=data['width']):continue
                if not (endr<=tr or ar>br or endc<=tc or ac>bc):continue
                positions=[]
                for block in data['blocks']:
                    dr,dc=block['bbox'][0]-ar,block['bbox'][1]-ac
                    if dr<0 or dc<0 or dr%pitch or dc%pitch:break
                    r,c=dr//pitch,dc//pitch
                    if not (r<nr and c<nc and pattern[r][c]==block['color']):break
                    positions.append([r,c])
                else:
                    candidates.append({'origin':[ar,ac],'pitch':pitch,'seed_cells':positions})
    return candidates


def infer(g):
    data=extract(g);choices=registrations(data)
    if len(choices)!=1:raise ValueError(f'expected one registration, found {len(choices)}')
    return {**data,**choices[0]}


def render(g,data,selected=None):
    out=[row[:] for row in g];ar,ac=data['origin'];pitch=data['pitch'];side=data['block_size']
    for r,row in enumerate(data['pattern']):
        for c,color in enumerate(row):
            if color==data['bg'] or (selected is not None and (r,c) not in selected):continue
            for dr in range(side):
                for dc in range(side):out[ar+r*pitch+dr][ac+c*pitch+dc]=color
    return out


def solve(g,completion='all'):
    if type(completion) is not str or completion not in ('all','anchored_components'):
        raise ValueError('completion must be all or anchored_components')
    data=infer(g)
    return render(g,data,selected_positions(data) if completion=='anchored_components' else None)


def pattern_components(pattern,bg,*,eight=False,color_sensitive=False):
    todo={(r,c) for r,row in enumerate(pattern) for c,v in enumerate(row) if v!=bg}
    comps=[]
    while todo:
        p=min(todo);todo.remove(p);stack=[p];comp={p};color=pattern[p[0]][p[1]]
        while stack:
            r,c=stack.pop()
            directions=((-1,0),(1,0),(0,-1),(0,1))
            if eight:directions=tuple((dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc)
            for dr,dc in directions:
                q=(r+dr,c+dc)
                if q in todo and (not color_sensitive or pattern[q[0]][q[1]]==color):
                    todo.remove(q);comp.add(q);stack.append(q)
        comps.append(comp)
    return comps


def selected_positions(data,*,eight=False,color_sensitive=False):
    anchors={tuple(p) for p in data['seed_cells']}
    return set().union(*(comp for comp in pattern_components(data['pattern'],data['bg'],eight=eight,
                       color_sensitive=color_sensitive) if comp & anchors))


def intermediate(g):
    data=infer(g)
    return {k:data[k] for k in ('origin','pitch','block_size','pattern','bg','seed_cells')} | {
        'selected_template_cells':[list(p) for p in sorted(selected_positions(data))]}


def make_scene(seed,index,height,width):
    """Construct a fresh registered pattern plus independent hidden ground truth.

    Colored seeds deliberately share a color with unrelated template cells.
    Their spatial relation, not a unique marker color, identifies registration.
    Geometry options are enumerated before drawing, with no unbounded retries.
    """
    from puzzle_generators.base import gen_ctx
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    integer(height,16,30,'height');integer(width,20,30,'width')
    rng=gen_ctx(seed=seed,sample_index=index,version='1.0.0',task_id='public_eval_c4d067a0').draw_rng('scene')
    options=[]
    for R in (4,5):
        for C in (3,4):
            for side in (2,3,4):
                for pitch in range(side+1,side+4):
                    for spacing in (2,3):
                        for transpose in (False,True):
                            nr,nc=(C,R) if transpose else (R,C)
                            mh,mw=(nr-1)*spacing+1,(nc-1)*spacing+1
                            bh,bw=(nr-1)*pitch+side,(nc-1)*pitch+side
                            if mh>height or mw>width or bh>height or bw>width:continue
                            for placement,ok in [('right',mw+1+bw<=width),('below',mh+1+bh<=height)]:
                                if ok:options.append((R,C,side,pitch,spacing,transpose,placement))
    if not options:raise ValueError('canvas cannot contain miniature plus reconstruction')
    preferred=[]
    if index==0:preferred=[o for o in options if o[:6]==(4,3,2,3,2,False)]
    if index==1:preferred=[o for o in options if o[:6]==(4,3,3,5,2,False)]
    if index==103 and height==width==30:preferred=[(5,3,4,5,2,False,'right')]
    R,C,side,pitch,spacing,transpose,placement=rng.choice(preferred or options)
    bg,A,B,COLOR,D=rng.sample(list(range(10)),5)
    cells={(0,0):A,(0,1):A,(1,0):B,(1,1):COLOR,(R-1,0):A}
    for r in range(2,R):cells[r,C-1]=D if r==R-1 else A
    if index>1 and rng.randrange(2):cells.pop((1,1))
    if C==4 and rng.randrange(2):cells[0,2]=B
    if C==4 and rng.randrange(2):cells[R-1,1]=D
    anchors=[(0,0),(0,1)]
    if index%2:anchors.append((2,C-1))
    flipr=True if index==0 else bool(rng.randrange(2))
    flipc=True if index==1 else bool(rng.randrange(2))
    def transform(p):
        r,c=p;r=R-1-r if flipr else r;c=C-1-c if flipc else c
        return (c,r) if transpose else (r,c)
    cells={transform(p):v for p,v in cells.items()};anchors=[transform(p) for p in anchors]
    nr,nc=(C,R) if transpose else (R,C)
    pattern=[[bg]*nc for _ in range(nr)]
    for (r,c),v in cells.items():pattern[r][c]=v
    mh,mw=(nr-1)*spacing+1,(nc-1)*spacing+1
    bh,bw=(nr-1)*pitch+side,(nc-1)*pitch+side
    if index==103 and height==width==30:
        mr,mc=1,1;ar,ac=height-bh,width-bw
    elif placement=='right':
        mr=rng.randint(0,min(2,height-mh));mc=rng.randint(0,min(2,width-mw-1-bw))
        ar=rng.randint(0,height-bh);ac=rng.randint(mc+mw+1,width-bw)
    else:
        mr=rng.randint(0,min(2,height-mh-1-bh));mc=rng.randint(0,min(2,width-mw))
        ar=rng.randint(mr+mh+1,height-bh);ac=rng.randint(0,width-bw)
    g=[[bg]*width for _ in range(height)]
    for (r,c),color in cells.items():g[mr+r*spacing][mc+c*spacing]=color
    for r,c in anchors:
        for dr in range(side):
            for dc in range(side):g[ar+r*pitch+dr][ac+c*pitch+dc]=pattern[r][c]
    scene={'input':g,'bg':bg,'pattern':pattern,'origin':[ar,ac],'pitch':pitch,
           'block_size':side,'seed_cells':[list(p) for p in anchors]}
    inferred=infer(g)
    if any(inferred[k]!=scene[k] for k in ('origin','pitch','block_size','pattern')):
        raise ValueError('constructed registration differs from inferred registration')
    return scene


def sample(seed,index,height,width):
    return make_scene(seed,index,height,width)['input']


# Canonical registration entry point. All dependencies below are mapped shared runtime.
from puzzle_generators.base import gen_ctx
GENERATOR_ID=TASK_ID='public_eval_c4d067a0'
RULE_TASK_ID = 'ee_c4d067a0'
VERSION='1.0.0'
SUMMARY='Infer square size, lattice pitch and unique alignment from partial enlarged evidence, then complete the miniature.'
EXAMPLES_NEEDED=2
MIN_STRICT_FRAC=1.0
AXES={'height':{'type':'int','valid':'16..30'},'width':{'type':'int','valid':'20..30'}}
INVARIANTS=['one miniature of singleton lattice cells','equal solid seed squares',
            'unique registration','template/target bounding boxes disjoint','background uniquely modal']
RULE_HASH = 'e418afd3bb42'

def generate(seed,sample_index,*,difficulty=None,**overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('unknown override')
    for k,v in overrides.items():integer(v,16 if k=='height' else 20,30,k)
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    height=ctx.draw_int_strict('height',16,30);width=ctx.draw_int_strict('width',20,30)
    return sample(seed,sample_index,height,width)


def self_check(grid,*,difficulty=None,meta=None):
    try:infer(grid)
    except (ValueError,TypeError) as exc:return [str(exc)]
    if isinstance(meta,dict):
        observed=observe_overrides(grid)
        return [f'{k} override not realized' for k,v in meta.get('overrides',{}).items() if observed.get(k)!=v]
    return []


def observe_overrides(grid):
    check_grid(grid)
    return {'height':len(grid),'width':len(grid[0])}


def rule_mirror(grid):return solve(grid,'all')
