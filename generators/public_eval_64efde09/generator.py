"""ARC 64efde09: transfer boundary-marker rays through oriented template copies.

General pattern matching, not original-grid lookup. Original datasets are never
read by this module. Outputs from rule_mirror are claims checked by Racket.
"""
from __future__ import annotations
RULE_TASK_ID = 'ee_64efde09'
from collections import Counter
from copy import deepcopy
from itertools import product
from puzzle_generators.base import gen_ctx

GENERATOR_ID = 'public_eval_64efde09'
TASK_ID = GENERATOR_ID
VERSION = '1.0.1'
SUMMARY = 'Match rotated/reflected multicolor bars and transfer colored boundary-marker rays to corresponding ports.'
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
AXES = {'scene_profile':{'type':'str','default':'mixed','valid':'compact|ordinary|stress'}}
INVARIANTS = ['unique modal background','3..4 full asymmetric multicolor 2-by-L stamps',
              'three distinct singleton boundary markers and corresponding ports',
              'noncrossing outward rays; all copies matched by exact D4 pattern']


def validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError('grid must have 1..30 rows')
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid must have 1..30 columns')
    w=len(grid[0])
    if any(type(row) is not list or len(row)!=w or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('rectangular exact-integer ARC grid required')


def turn_cell(p, k, h, w):
    r,c=p
    if k==0:return r,c
    if k==1:return c,h-1-r
    if k==2:return h-1-r,w-1-c
    if k==3:return w-1-c,r
    if k==4:return r,w-1-c
    if k==5:return c,r
    if k==6:return h-1-r,c
    if k==7:return w-1-c,h-1-r
    raise ValueError('D4 index must be 0..7')


def turn_grid(grid,k):
    h,w=len(grid),len(grid[0])
    oh,ow=(w,h) if k in (1,3,5,7) else (h,w)
    out=[[0]*ow for _ in range(oh)]
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            rr,cc=turn_cell((r,c),k,h,w); out[rr][cc]=v
    return out


def analyze(grid):
    validate_grid(grid)
    counts=Counter(v for row in grid for v in row)
    bg=min(counts,key=lambda c:(-counts[c],c))
    remaining={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg}
    bars=[]; seeds=[]
    while remaining:
        start=min(remaining); remaining.remove(start); stack=[start]; cells={start}
        while stack:
            r,c=stack.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in remaining: remaining.remove(p); cells.add(p); stack.append(p)
        if len(cells)==1:
            r,c=start
            directions=[]
            if r==0:directions.append((-1,0))
            if r==len(grid)-1:directions.append((1,0))
            if c==0:directions.append((0,-1))
            if c==len(grid[0])-1:directions.append((0,1))
            seeds.append({'cell':start,'color':grid[r][c],'outward_normals':directions})
            continue
        r0,r1=min(r for r,c in cells),max(r for r,c in cells)
        c0,c1=min(c for r,c in cells),max(c for r,c in cells)
        bars.append({'bbox':(r0,c0,r1,c1),'cells':cells,
                     'pattern':[row[c0:c1+1] for row in grid[r0:r1+1]]})
    return bg,bars,seeds


def source_connection(seed,bars):
    r,c=seed['cell']; candidates=[]
    for index,bar in enumerate(bars):
        r0,c0,r1,c1=bar['bbox']; hh,ww=r1-r0+1,c1-c0+1
        if hh>ww and r0<=r<=r1:
            if c<c0:candidates.append({'gap':c0-c,'source_index':index,'contact':(r-r0,0),'normal':(0,-1)})
            if c>c1:candidates.append({'gap':c-c1,'source_index':index,'contact':(r-r0,ww-1),'normal':(0,1)})
        if ww>hh and c0<=c<=c1:
            if r<r0:candidates.append({'gap':r0-r,'source_index':index,'contact':(0,c-c0),'normal':(-1,0)})
            if r>r1:candidates.append({'gap':r-r1,'source_index':index,'contact':(hh-1,c-c0),'normal':(1,0)})
    candidates=[p for p in candidates if p['normal'] in seed['outward_normals']]
    if not candidates:raise ValueError('boundary marker has no bar along its inward normal')
    return min(candidates,key=lambda p:(p['gap'],p['source_index']))


def plans(grid):
    bg,bars,seeds=analyze(grid); rays=[]
    for si,seed in enumerate(seeds):
        try:conn=source_connection(seed,bars)
        except ValueError:continue
        source=bars[conn['source_index']]; pattern=source['pattern']
        hh,ww=len(pattern),len(pattern[0]); q=conn['contact']; nr,nc=conn['normal']
        for ti,target in enumerate(bars):
            codes=[k for k in range(8) if turn_grid(pattern,k)==target['pattern']]
            if not codes:continue
            code=codes[0]; tr,tc=turn_cell(q,code,hh,ww)
            ur,uc=turn_cell((q[0]+nr,q[1]+nc),code,hh,ww)
            r0,c0,r1,c1=target['bbox']
            rays.append({'color':seed['color'],'seed_index':si,'source_index':conn['source_index'],
                'target_index':ti,'source_gap':conn['gap'],'code':code,
                'contact':(r0+tr,c0+tc),'normal':(ur-tr,uc-tc),
                'target_bbox':target['bbox'],'source_offset':q[0] if hh>ww else q[1]})
    return bg,rays


def ray_cells(grid,bg,ray,extent,*,port_rule='matched',length_override=None):
    r,c=ray['contact']; dr,dc=ray['normal']; r0,c0,r1,c1=ray['target_bbox']
    if port_rule=='same_index':
        if dr==0:r=r0+ray['source_offset']
        else:c=c0+ray['source_offset']
    elif port_rule=='reverse':
        if dr==0:r=r0+r1-r
        else:c=c0+c1-c
    elif port_rule!='matched':raise ValueError('unknown port rule')
    length=len(grid)+len(grid[0]) if extent=='boundary' else ray['source_gap']
    if length_override is not None:length=length_override
    cells=[]
    for _ in range(length):
        r+=dr;c+=dc
        if not (0<=r<len(grid) and 0<=c<len(grid[0])):break
        if grid[r][c] not in (bg,ray['color']):break
        cells.append((r,c))
    return cells


def solve(grid,extent='boundary',*,port_rule='matched',scope='all',length_override=None):
    if extent not in ('boundary','source_length'):raise ValueError('unknown ray extent')
    bg,rays=plans(grid); out=deepcopy(grid)
    for ray in rays:
        if scope=='source_only' and ray['target_index']!=ray['source_index']:continue
        if scope=='first_seed' and ray['seed_index']!=0:continue
        if scope=='rotations_only' and ray['code']>=4:continue
        if scope not in ('all','source_only','first_seed','rotations_only'):raise ValueError('unknown scope')
        for r,c in ray_cells(grid,bg,ray,extent,port_rule=port_rule,length_override=length_override):out[r][c]=ray['color']
    return out


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index<0:
        raise TypeError('exact integer seed and nonnegative sample index required')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('unknown override')
    profile=overrides.get('scene_profile')
    if profile is not None and profile not in ('compact','ordinary','stress'):raise ValueError('unknown profile')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,task_id=TASK_ID,version=VERSION,difficulty=difficulty,overrides=overrides)
    choices=[profile] if profile is not None else (['stress'] if sample_index==103 else ['compact','ordinary'])
    profile=ctx.draw_choice('scene_profile',choices)
    rng=ctx.draw_rng('geometry'); bg=ctx.draw_choice('background',list(range(10)))
    palette=[c for c in range(10) if c!=bg]; rng.shuffle(palette)
    ncolors=rng.choice((3,4)); colors=palette[:ncolors]; marker_colors=palette[ncolors:ncolors+3]
    if profile=='stress':h=w=30;length=14
    elif profile=='compact':h=rng.randint(24,26);w=rng.randint(24,26);length=rng.randint(5,8)
    else:h=rng.randint(26,29);w=rng.randint(26,29);length=rng.randint(7,10)
    # Asymmetric endpoint coding and a distinct broad face identify handedness.
    a,b,base=colors[:3]; end=colors[-1]
    pattern=[[a]+[rng.choice((a,b)) for _ in range(length-3)]+[end,end],
             [base]*(length-1)+[end]]
    assert sum(turn_grid(pattern,k)==pattern for k in range(8))==1
    gaps=[2,3,4,5];rng.shuffle(gaps);gt,gb,gl,gr=gaps
    cmin,cmax=gl+3,w-gr-3-length
    rmin,rmax=gt+3,h-gb-3-length
    assert cmin<=cmax and rmin<=rmax
    specs=[('top',gt,rng.randint(cmin,cmax),rng.choice((2,6)),gt),
           ('bottom',h-gb-2,rng.randint(cmin,cmax),rng.choice((0,4)),gb),
           ('left',rng.randint(rmin,rmax),gl,rng.choice((1,7)),gl),
           ('right',rng.randint(rmin,rmax),w-gr-2,rng.choice((3,5)),gr)]
    if profile!='stress' and rng.randrange(2):specs.pop(rng.randrange(4))
    # Every individual scene teaches both reflection and longitudinal reversal.
    # Enumerate the tiny legal orientation space rather than rejection-sampling
    # lessons until they happen to show the relevant contrast.
    options={'top':(2,6),'bottom':(0,4),'left':(1,7),'right':(3,5)}
    legal=[codes for codes in product(*(options[item[0]] for item in specs))
           if len({code>=4 for code in codes})==2
           and len({code in (2,3,4,7) for code in codes})==2]
    codes=rng.choice(legal)
    specs=[(name,r0,c0,code,gap) for (name,r0,c0,_,gap),code in zip(specs,codes)]
    grid=[[bg]*w for _ in range(h)]
    for _,r0,c0,code,gap in specs:
        tile=turn_grid(pattern,code)
        for r,row in enumerate(tile):
            for c,v in enumerate(row):
                if grid[r0+r][c0+c]!=bg:raise AssertionError('stamp collision')
                grid[r0+r][c0+c]=v
    shortest=min(range(len(specs)),key=lambda i:specs[i][4])
    others=[i for i in range(len(specs)) if i!=shortest];rng.shuffle(others)
    sources=[shortest]+others[:2];ports=rng.sample(list(range(length)),3)
    for source,offset,color in zip(sources,ports,marker_colors):
        _,r0,c0,code,gap=specs[source]
        rr,cc=turn_cell((1,offset),code,2,length)
        ur,uc=turn_cell((2,offset),code,2,length);dr,dc=ur-rr,uc-cc
        r,c=r0+rr+dr*gap,c0+cc+dc*gap
        assert r in (0,h-1) or c in (0,w-1)
        if grid[r][c]!=bg:raise AssertionError('marker collision')
        grid[r][c]=color
    errors=self_check(grid)
    if errors:raise RuntimeError('; '.join(errors))
    return grid


def self_check(grid,*,difficulty=None,meta=None):
    try:bg,bars,seeds=analyze(grid)
    except (ValueError,TypeError) as exc:return [str(exc)]
    errors=[];counts=Counter(v for row in grid for v in row)
    if sum(n==counts[bg] for n in counts.values())!=1:errors.append('ambiguous background')
    if not 3<=len(bars)<=4:errors.append('expected 3..4 stamps')
    if len(seeds)!=3 or len({s['color'] for s in seeds})!=3:errors.append('expected three distinct boundary markers')
    for bar in bars:
        hh,ww=len(bar['pattern']),len(bar['pattern'][0])
        if min(hh,ww)!=2 or not 5<=max(hh,ww)<=14 or len(bar['cells'])!=hh*ww:errors.append('stamp must be a full 2-by-L rectangle')
        if sum(turn_grid(bars[0]['pattern'],k)==bar['pattern'] for k in range(8))!=1:errors.append('missing or ambiguous D4 correspondence')
    for s in seeds:
        r,c=s['cell']
        if not(r in (0,len(grid)-1) or c in (0,len(grid[0])-1)):errors.append('marker must be on boundary')
        try:
            if source_connection(s,bars)['gap']<2:errors.append('marker too near stamp')
        except ValueError as exc:errors.append(str(exc))
    if errors:return errors
    _,rays=plans(grid); owners={}
    if len(rays)!=len(bars)*len(seeds):errors.append('missing ray correspondence')
    if len({p['code']>=4 for p in rays})!=2:errors.append('reflection contrast missing')
    if not any((p['contact'][0]-p['target_bbox'][0] if p['normal'][0]==0 else
                p['contact'][1]-p['target_bbox'][1])!=p['source_offset'] for p in rays):
        errors.append('longitudinal port-reversal contrast missing')
    for ray in rays:
        for p in ray_cells(grid,bg,ray,'boundary'):
            if p in owners and owners[p]!=ray['color']:errors.append('crossing colored rays')
            owners[p]=ray['color']
    if solve(grid,'boundary')==solve(grid,'source_length'):errors.append('extent settings not distinguishable')
    return errors


rule_mirror=solve
strict_canonical_like=self_check
