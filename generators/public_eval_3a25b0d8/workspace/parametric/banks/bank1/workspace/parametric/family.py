"""Transfer compartment colors from a filled figure to a blank figure.

Self-contained: only standard-library imports, including after relocation.
Figures can differ in shape/size; relative side and vertical order carry color.
Racket independently executes reference labels.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import random

GENERATOR_ID = TASK_ID = 'public_eval_3a25b0d8'
RULE_TASK_ID = 'ee_3a25b0d8'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
SUMMARY = 'Extract enclosed compartments, match left/center/right lanes in vertical order and transfer colors to the blank outline.'
INVARIANTS = ['unique modal background', 'two separate 8-connected figures', 'one monochrome template', '4-connected enclosed regions', 'equal lane cardinalities and pure source-region colors']
AXES = {}
POLICIES = ('aligned','reverse_vertical')


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid_check(grid):
    if type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('grid must have 1..30 rows and columns')
    w=len(grid[0])
    if any(type(row) is not list or len(row)!=w or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('grid must be rectangular exact ARC integers')


def components(cells,diagonal=False):
    cells=set(cells);out=[]
    deltas=((-1,0),(1,0),(0,-1),(0,1))
    if diagonal:deltas+=((-1,-1),(-1,1),(1,-1),(1,1))
    while cells:
        p=min(cells);cells.remove(p);todo=[p];part=[]
        while todo:
            r,c=todo.pop();part.append((r,c))
            for dr,dc in deltas:
                q=(r+dr,c+dc)
                if q in cells:cells.remove(q);todo.append(q)
        out.append(sorted(part))
    return out


def bbox(cells):
    rr,cc=zip(*cells)
    return min(rr),min(cc),max(rr),max(cc)


def isolate(grid,cells,bg):
    r0,c0,r1,c1=bbox(cells)
    out=[[bg]*(c1-c0+1) for _ in range(r1-r0+1)]
    for r,c in cells:out[r-r0][c-c0]=grid[r][c]
    return out


def regions(crop,outline,diagonal=False):
    h,w=len(crop),len(crop[0]);out=[]
    cells=[(r,c) for r in range(h) for c in range(w) if crop[r][c]!=outline]
    for part in components(cells,diagonal):
        r0,c0,r1,c1=bbox(part)
        if r0==0 or c0==0 or r1==h-1 or c1==w-1:continue
        value=2*sum(c for r,c in part)-(w-1)*len(part)
        side=(value>0)-(value<0)
        colors=sorted({crop[r][c] for r,c in part})
        out.append(dict(cells=part,side=side,box=(r0,c0,r1,c1),colors=colors))
    return sorted(out,key=lambda o:(o['side'],o['box'][0],o['box'][1]))


def parse(grid):
    grid_check(grid);freq=Counter(v for row in grid for v in row);bg=freq.most_common(1)[0][0]
    if sum(n==freq[bg] for n in freq.values())!=1:raise ValueError('background must be the unique mode')
    figures=components([(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg],True)
    if len(figures)!=2:raise ValueError('requires two separate figures')
    palettes=[{grid[r][c] for r,c in fig} for fig in figures]
    choices=[i for i,colors in enumerate(palettes) if len(colors)==1]
    if len(choices)!=1:raise ValueError('requires exactly one blank outline')
    t=choices[0];s=1-t;outline=next(iter(palettes[t]))
    if outline not in palettes[s]:raise ValueError('figures must share an outline color')
    template=isolate(grid,figures[t],bg);source=isolate(grid,figures[s],bg)
    target_regions=regions(template,outline);source_regions=regions(source,outline)
    if not source_regions or len(source_regions)!=len(target_regions):raise ValueError('compartment counts differ')
    if Counter(o['side'] for o in source_regions)!=Counter(o['side'] for o in target_regions):raise ValueError('lane cardinalities differ')
    if any(o['colors']!=[bg] for o in target_regions):raise ValueError('template must be blank')
    if any(len(o['colors'])!=1 or o['colors'][0] in (bg,outline) for o in source_regions):raise ValueError('source compartment must have one non-background color')
    return dict(background=bg,outline=outline,template=template,source=source,
                target_regions=target_regions,source_regions=source_regions)


def assign(state,policy):
    source=state['source_regions'];out=[]
    for lane in (-1,0,1):
        part=[o for o in source if o['side']==lane]
        if policy=='reverse_vertical':part=list(reversed(part))
        out.extend(o['colors'][0] for o in part)
    return out


def paint(state,colors):
    out=deepcopy(state['template'])
    for obj,color in zip(state['target_regions'],colors):
        for r,c in obj['cells']:out[r][c]=color
    return out


def solve(grid,color_order='aligned'):
    if color_order not in POLICIES:raise ValueError('unknown color order')
    state=parse(grid)
    return paint(state,assign(state,color_order))


rule_mirror=solve


def self_check(grid,*,difficulty=None,meta=None):
    try:parse(grid)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []


def hole_mask(h,w,kind):
    # Symmetric about the column axis; center-lane membership is exact even
    # when the source and target use different interior shapes.
    if w==1:return [(r,0) for r in range(h)]
    if kind==0 or h<3 or w==2:return [(r,c) for r in range(h) for c in range(w)]
    if kind==1:return [(r,c) for r in range(h) for c in range(w) if r==h//2 or c==w//2]
    if kind==2:return [(r,c) for r in range(h) for c in range(w) if r==0 or r==1 or c==w//2]
    return [(r,c) for r in range(h) for c in range(w) if r==h-1 or r==h-2 or c==w//2]


def figure(width,band_height,gaps,colors,bg,outline,rng,kind_offset,stagger=False):
    bands=len(gaps)+1;h=bands*band_height+sum(gaps)
    out=[[bg]*width for _ in range(h)];top=0
    for b in range(bands):
        for r in range(top,top+band_height):
            for c in range(width):out[r][c]=outline
        # Open corners are exterior; the adjacent interior remains 4-enclosed.
        for r,c in ((top,0),(top,width-1),(top+band_height-1,0),(top+band_height-1,width-1)):
            out[r][c]=bg
        if width==13:starts=(1,5,9);widths=(3,3,3)
        elif width==11:starts=(1,4,8);widths=(2,3,2)
        else:starts=(1,width//2,width-2);widths=(1,1,1)
        for lane,(col,ww) in enumerate(zip(starts,widths)):
            hh=band_height-2;hole_top=top+1
            # Source and target deliberately disagree on raw region discovery
            # order. Side+vertical correspondence, not scan order, carries color.
            if stagger and b==0 and hh>=2:
                hh-=1
                hole_top+=int((lane==1)==(kind_offset==2))
            kind=(b+lane+kind_offset+rng.randrange(2))%4
            shape=hole_mask(hh,ww,kind)
            for r,c in shape:out[hole_top+r][col+c]=colors[b][lane]
        top+=band_height
        if b<len(gaps):
            for r in range(top,top+gaps[b]):out[r][width//2]=outline
            top+=gaps[b]
    return out


# Input H,W; figure width; band height; source gaps; target gaps.
# Different vertical spacing forces correspondence rather than pixel copying.
PROFILES=(
 (27,27,11,5,(1,9),(9,1)),
 (28,30,13,5,(2,4),(4,2)),
 (26,28,11,5,(2,3),(4,1)),
 (28,29,13,5,(1,5),(3,4)),
 (24,26,11,4,(3,2),(1,5)),
 (29,30,13,5,(2,2),(5,2)),
 (18,23,9,4,(2,),(5,)),
 (24,27,11,5,(2,1),(1,3)),
 (28,29,13,5,(3,3),(1,6)),
 (30,30,13,5,(1,1,1),(3,3,4)),
)


def make_scene(seed,profile):
    integer(seed,0,2**63-1,'seed');integer(profile,0,9,'profile')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'compartments:{seed}:{profile}'.encode()).digest(),'big'))
    h,w,fw,bh,sg,tg=PROFILES[profile]
    bg,outline=rng.sample(range(10),2)
    palette=[c for c in range(10) if c not in (bg,outline)];rng.shuffle(palette)
    n=len(sg)+1
    colors=[[palette[(b*3+j)%len(palette)] for j in range(3)] for b in range(n)]
    source=figure(fw,bh,sg,colors,bg,outline,rng,0,profile in (0,1,7))
    target=figure(fw,bh,tg,[[bg]*3 for _ in range(n)],bg,outline,rng,2,profile in (0,1,7))
    pieces=[source,target];rng.shuffle(pieces)
    separation=2;left=rng.randrange(w-2*fw-separation+1)
    out=[[bg]*w for _ in range(h)]
    for i,piece in enumerate(pieces):
        row=rng.randrange(h-len(piece)+1);col=left+i*(fw+separation)
        for r,line in enumerate(piece):
            for c,v in enumerate(line):out[row+r][col+c]=v
    parse(out)
    return out


def generate(seed=0,sample_index=0,*,difficulty=None,**overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if overrides:raise ValueError('unknown overrides: '+','.join(sorted(overrides)))
    return make_scene(seed,sample_index%10)


RIVALS=('copy_template','copy_exemplar','reverse_instead','aligned_instead','global_reading_order',
        'mirror_lanes','dominant_fill','numeric_palette','nearest_centroid','paint_exterior','diagonal_open')


def rival(grid,policy,name):
    s=parse(grid);src=s['source_regions'];trg=s['target_regions'];colors=assign(s,policy)
    if name=='copy_template':return deepcopy(s['template'])
    if name=='copy_exemplar':return deepcopy(s['source'])
    if name=='reverse_instead':colors=assign(s,'reverse_vertical')
    elif name=='aligned_instead':colors=assign(s,'aligned')
    elif name=='global_reading_order':
        so=sorted(src,key=lambda o:(o['box'][0],o['box'][1]));to=sorted(range(len(trg)),key=lambda i:(trg[i]['box'][0],trg[i]['box'][1]))
        if policy=='reverse_vertical':so=list(reversed(so))
        colors=[None]*len(trg)
        for i,o in zip(to,so):colors[i]=o['colors'][0]
    elif name=='mirror_lanes':
        colors=[]
        for lane in (-1,0,1):
            so=[o for o in src if o['side']==-lane]
            if policy=='reverse_vertical':so.reverse()
            colors.extend(o['colors'][0] for o in so)
    elif name=='dominant_fill':
        counts=Counter()
        for o in src:counts[o['colors'][0]]+=len(o['cells'])
        colors=[counts.most_common(1)[0][0]]*len(trg)
    elif name=='numeric_palette':
        palette=sorted({o['colors'][0] for o in src});colors=[palette[i%len(palette)] for i in range(len(trg))]
    elif name=='nearest_centroid':
        def centroid(o,g):
            return (sum(r for r,c in o['cells'])/len(o['cells'])/(len(g)-1),sum(c for r,c in o['cells'])/len(o['cells'])/(len(g[0])-1))
        colors=[]
        for target in trg:
            a=centroid(target,s['template'])
            choices=[o for o in src if o['side']==target['side']]
            best=min(choices,key=lambda o:sum((x-y)**2 for x,y in zip(a,centroid(o,s['source']))))
            colors.append(best['colors'][0])
    elif name=='paint_exterior':
        out=paint(s,colors)
        return [[colors[0] if v==s['background'] else v for v in row] for row in out]
    elif name=='diagonal_open':
        enclosed={p for o in regions(s['template'],s['outline'],True) for p in o['cells']}
        out=paint(s,colors)
        for o in trg:
            for r,c in o['cells']:
                if (r,c) not in enclosed:out[r][c]=s['background']
        return out
    elif name not in ('copy_template','copy_exemplar'):raise ValueError(name)
    return paint(s,colors)
