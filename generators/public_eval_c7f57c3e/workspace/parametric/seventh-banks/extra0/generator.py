"""Scale-normalized motif substitution for public parent c7f57c3e.

Blue (1) is the shared alignment skeleton. Background is the unique modal
color. The admitted grammar has two block-scaled motifs with an identical
primitive blue mask, separated under eight-connectivity. Templates are bound
relative to the blue origin, so an accent can move above/below/left/right.
Python is a claim mirror; protected Racket is the separate label authority.
"""
from collections import Counter
import copy
import math

TASK_ID='public_eval_c7f57c3e'
SETTINGS=('exchange','minority')
DELTAS=tuple((dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc)

def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value

def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list
            or not 1<=len(g[0])<=30 or any(type(row) is not list or len(row)!=len(g[0])
            or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('grid must be rectangular 1..30 with exact colors 0..9')

def components(cells):
    unseen=set(cells);result=[]
    while unseen:
        root=min(unseen);unseen.remove(root);part={root};stack=[root]
        while stack:
            r,c=stack.pop()
            for dr,dc in DELTAS:
                p=(r+dr,c+dc)
                if p in unseen:unseen.remove(p);part.add(p);stack.append(p)
        result.append(part)
    return result

def blue_scale(blue):
    lengths=[]
    for r,c in blue:
        for dr,dc in ((0,1),(1,0)):
            if (r-dr,c-dc) not in blue:
                n=1
                while (r+n*dr,c+n*dc) in blue:n+=1
                lengths.append(n)
    return math.gcd(*lengths)

def parse(g):
    grid_check(g);h,w=len(g),len(g[0]);frequencies=Counter(v for row in g for v in row)
    ranking=frequencies.most_common()
    if len(ranking)<3 or ranking[0][1]==ranking[1][1] or ranking[0][0]==1:
        raise ValueError('unique modal nonblue background and colored motifs required')
    bg=ranking[0][0];objects=[];templates=[]
    for cells in components((r,c) for r in range(h) for c in range(w) if g[r][c]!=bg):
        blue={p for p in cells if g[p[0]][p[1]]==1}
        if not blue:raise ValueError('every motif must contain the blue skeleton')
        n=blue_scale(blue);ar=min(r for r,c in blue);ac=min(c for r,c in blue)
        signature=tuple(sorted({((r-ar)//n,(c-ac)//n,g[r][c]) for r,c in cells}))
        expanded={(ar+r*n+dr,ac+c*n+dc):v for r,c,v in signature for dr in range(n) for dc in range(n)}
        if set(expanded)!=cells or any(g[r][c]!=v for (r,c),v in expanded.items()):
            raise ValueError('motif is not aligned homogeneous block scaling')
        if signature not in templates:templates.append(signature)
        objects.append({'cells':cells,'scale':n,'origin':(ar,ac),'template':templates.index(signature)})
    if len(templates)!=2:raise ValueError('exactly two normalized colored motifs required')
    blues=[tuple((r,c) for r,c,v in t if v==1) for t in templates]
    if blues[0]!=blues[1]:raise ValueError('normalized blue skeletons must match')
    # The complete union footprint must be lawful for either substitution.
    used={}
    for i,obj in enumerate(objects):
        ar,ac=obj['origin'];n=obj['scale']
        for r,c,v in set(templates[0])|set(templates[1]):
            for dr in range(n):
                for dc in range(n):
                    p=(ar+r*n+dr,ac+c*n+dc)
                    if not(0<=p[0]<h and 0<=p[1]<w):raise ValueError('substituted motif would leave canvas')
                    if p in used and used[p]!=i:raise ValueError('substituted motifs would overlap')
                    used[p]=i
    counts=[sum(o['template']==i for o in objects) for i in range(2)]
    return {'background':bg,'templates':templates,'objects':objects,'counts':counts,'blue_mask':blues[0]}

def render(g,p,choices,*,unit_scale=False,align_bbox=False):
    out=[[p['background']]*len(g[0]) for _ in g]
    for obj,target in zip(p['objects'],choices):
        n=1 if unit_scale else obj['scale'];ar,ac=obj['origin'];template=p['templates'][target]
        if align_bbox:
            ar=min(r for r,c in obj['cells'])-min(r for r,c,v in template)*n
            ac=min(c for r,c in obj['cells'])-min(c for r,c,v in template)*n
        for r,c,v in template:
            for dr in range(n):
                for dc in range(n):
                    rr,cc=ar+r*n+dr,ac+c*n+dc
                    if 0<=rr<len(g) and 0<=cc<len(g[0]):out[rr][cc]=v
    return out

def solve(g,mode='exchange'):
    if type(mode) is not str or mode not in SETTINGS:raise ValueError('mode must be exchange or minority')
    p=parse(g)
    # Equal frequencies use the first row-major discovered motif; ordinary
    # lessons additionally include unequal frequencies to expose the count rule.
    target=0 if p['counts'][0]<=p['counts'][1] else 1
    choices=[1-o['template'] if mode=='exchange' else target for o in p['objects']]
    return render(g,p,choices)

def self_check(g):
    try:parse(g);return []
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]

def _motifs(rng, stress=False):
    archetypes=[
        ({(0,1),(1,0),(1,2)}, {(1,1)}, {(-1,1)}, {(2,1),(3,0),(3,1),(3,2)}),
        ({(0,0),(0,2),(2,0),(2,2)}, {(1,1)}, {(-1,1)}, {(3,1)}),
        ({(0,1),(0,2),(1,0),(1,3),(2,1),(2,2)}, {(1,1),(1,2)}, {(-1,1),(-1,2)}, {(3,1),(3,2)}),
        ({(r,c) for r in range(3) for c in range(3) if (r,c)!=(1,1)}, {(1,1)}, {(-1,1)}, {(3,0),(3,1),(3,2)}),
    ]
    blue,core,top,bottom=archetypes[rng.choice((2,3)) if stress else rng.randrange(4)]
    palette=rng.sample([c for c in range(10) if c!=1],5)
    bg,ca,cb,ta,tb=palette
    # Some scenes change only the external appendage; others change the core too.
    if rng.randrange(2):cb=ca
    a={p:1 for p in blue}|{p:ca for p in core}|{p:ta for p in top}
    b={p:1 for p in blue}|{p:cb for p in core}|{p:tb for p in bottom}
    turns=rng.randrange(4);flip=bool(rng.randrange(2))
    def transform(p):
        r,c=p
        if flip:c=-c
        for _ in range(turns):r,c=c,-r
        return r,c
    transformed=[{transform(p):v for p,v in t.items()} for t in (a,b)]
    blue2=[p for p,v in transformed[0].items() if v==1]
    ar=min(r for r,c in blue2);ac=min(c for r,c in blue2)
    return bg,[{(r-ar,c-ac):v for (r,c),v in t.items()} for t in transformed]

def scene(seed,index,kind='demo'):
    """Construct bounded, separated union footprints before rendering inputs."""
    integer(seed,0,2**63-1,'seed');integer(index,0,1000000,'index')
    if kind not in ('demo','query'):raise ValueError('kind must be demo or query')
    from puzzle_generators.base import gen_ctx
    ctx=gen_ctx(seed=seed,sample_index=index,version='1.0.0',task_id=TASK_ID)
    rng=ctx.draw_rng(kind+'-motif-scene')
    stress=kind=='query' and index==3
    bg,templates=_motifs(rng,stress)
    union=set(templates[0])|set(templates[1]);r0=min(r for r,c in union);c0=min(c for r,c in union)
    uh=max(r for r,c in union)-r0+1;uw=max(c for r,c in union)-c0+1
    if kind=='demo' and index<2:
        # Teach count selection with minority last/large, then first/small.
        labels=[0,0,1] if index==0 else [1,0,0]
        scales=[1,1,3 if index==0 else 2]
    else:
        total=5 if stress else 3+index%3
        minority_count=2 if total==5 and not stress else 1
        labels=[0]*(total-minority_count)+[1]*minority_count
        rng.shuffle(labels)
        scales=[1]*(total-1)+[3 if stress or index%2==1 else 2]
        if total==4 and index%2==0:scales[1]=2
    small=len(labels)-1
    widths=[uw*n for n in scales[:-1]]
    gap=2
    topwidth=sum(widths)+gap*(small-1)
    y_offsets=[0]*small
    if kind=='demo' and index==1:y_offsets[1]=3
    topheight=max(uh*n+off for n,off in zip(scales[:-1],y_offsets))
    bottomscale=scales[-1]
    height=30 if stress else topheight+gap+uh*bottomscale+2
    width=30 if stress else max(topwidth,uw*bottomscale)+2+rng.randrange(3)
    if height>30 or width>30:raise ValueError('layout exceeds ARC canvas')
    g=[[bg]*width for _ in range(height)]
    slots=[];x=0 if stress else 1
    if stress:
        # Four small copies span the top, not a tiny pattern padded to 30x30.
        xs=[round(i*(30-uw)/(small-1)) for i in range(small)]
    else:
        xs=[]
        for ww in widths:xs.append(x);x+=ww+gap
    for i in range(small):slots.append((y_offsets[i]+(0 if stress else 1),xs[i]))
    slots.append((height-uh*bottomscale-(0 if stress else 1),rng.randrange(width-uw*bottomscale+1)))
    for label,n,(ur,uc) in zip(labels,scales,slots):
        for (r,c),v in templates[label].items():
            for dr in range(n):
                for dc in range(n):g[ur+(r-r0)*n+dr][uc+(c-c0)*n+dc]=v
    # The two teaching contrasts keep deliberate discovery order; other scenes
    # freely rotate/reflect the entire layout as well as the motif itself.
    if kind=='query' or index>=2:
        if rng.randrange(2):g=[row[::-1] for row in g]
        for _ in range(rng.randrange(4)):g=[list(row) for row in zip(*g[::-1])]
    parse(g)
    return g

def rivals(g,mode):
    """Total executable rivals on the admitted grammar, never error-as-evidence."""
    p=parse(g);objs=p['objects'];ids=[o['template'] for o in objs]
    counts=p['counts'];least=0 if counts[0]<=counts[1] else 1;most=1-least
    choices=[1-i for i in ids] if mode=='exchange' else [least]*len(ids)
    totals=[sum(len(o['cells']) for o in objs if o['template']==i) for i in (0,1)]
    area_target=0 if totals[0]<=totals[1] else 1
    largest=max(objs,key=lambda o:len(o['cells']))['template']
    smallest=min(objs,key=lambda o:len(o['cells']))['template']
    maxscale=max(o['scale'] for o in objs)
    result={
        'identity':copy.deepcopy(g),
        'other_setting':solve(g,'minority' if mode=='exchange' else 'exchange'),
        'first_template':render(g,p,[0]*len(ids)),
        'last_template':render(g,p,[1]*len(ids)),
        'majority_template':render(g,p,[most]*len(ids)),
        'least_pixel_area':render(g,p,[area_target]*len(ids)),
        'largest_object_template':render(g,p,[largest]*len(ids)),
        'smallest_object_template':render(g,p,[smallest]*len(ids)),
        'unit_scale':render(g,p,choices,unit_scale=True),
        'bbox_alignment':render(g,p,choices,align_bbox=True),
        'leave_enlarged_unchanged':render(g,p,[i if o['scale']>1 else t for i,o,t in zip(ids,objs,choices)]),
        'only_largest_scale':render(g,p,[t if o['scale']==maxscale else i for i,o,t in zip(ids,objs,choices)]),
    }
    return result

RULE_TASK_ID = 'ee_c7f57c3e'
VERSION='1.0.0'
GENERATOR_ID=TASK_ID
AXES={}
SUMMARY='Exchange two scale-normalized motifs while preserving their blue alignment skeletons.'
RULE_HASH='4c495bffb46ca60ffb4e130623bb3890c2f8d5984238dd5150451eaed53c8a86'
def get_info():
    return {'task_id':TASK_ID,'generator_id':TASK_ID,'version':VERSION,'summary':SUMMARY,'rule_hash':RULE_HASH,'axes':AXES}
def generate(seed,sample_index=0,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard') or overrides:raise ValueError('unsupported difficulty or override')
    return scene(seed,sample_index,'demo')
def generate_input(ctx):
    if getattr(ctx,'overrides',{}):raise ValueError('no explicit axes')
    return generate(ctx.seed,ctx.sample_index,difficulty=getattr(ctx,'difficulty',None))
def rule_mirror(g):return solve(g,'exchange')
