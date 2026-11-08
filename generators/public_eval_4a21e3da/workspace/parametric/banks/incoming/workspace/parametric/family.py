"""Boundary-marker cuts, corner docking, and occupied-area sector selection.

General algorithms only: no original grid, solution, task-data import or seed
lookup is used in solving. The exact observed 1/2/7 palette is retained.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import copy
import hashlib
import json
import random

HERE=Path(__file__).resolve().parent
VALUES=('all','largest')
RIVALS=('all_sectors','largest_sector','smallest_sector','first_sector','last_sector',
        'bbox_area','all_corners','split_components','global_bbox','no_move',
        'no_rays','whole_canvas_rays','first_hit_rays')

def integer(v,lo,hi,name):
    if type(v) is not int or not lo<=v<=hi: raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return v

def validate_grid(g):
    if (type(g) is not list or not 3<=len(g)<=30 or type(g[0]) is not list or not 3<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or any(type(x) is not int or x not in (1,2,7) for x in row) for row in g)):
        raise ValueError('Need rectangular 3..30 integer grid in palette 1,2,7')

def bbox(points):
    return min(r for r,c in points),min(c for r,c in points),max(r for r,c in points),max(c for r,c in points)

def components(points):
    left=set(points);result=[]
    while left:
        p=min(left);left.remove(p);part={p};q=[p]
        for r,c in q:
            for t in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if t in left:left.remove(t);part.add(t);q.append(t)
        result.append(part)
    return result

def parse(g,all_corners=False,split_components=False):
    validate_grid(g);h,w=len(g),len(g[0])
    fg={(r,c) for r in range(h) for c in range(w) if g[r][c]==7}
    marks=[(r,c) for r in range(h) for c in range(w) if g[r][c]==2]
    if not fg or not 1<=len(marks)<=2:raise ValueError('Need foreground and one or two edge markers')
    vertical=[];horizontal=[]
    for r,c in marks:
        if r in (0,h-1) and 0<c<w-1:vertical.append((r,c))
        elif c in (0,w-1) and 0<r<h-1:horizontal.append((r,c))
        else:raise ValueError('Markers must lie on an edge, not at a corner')
    if len(vertical)>1 or len(horizontal)>1:raise ValueError('At most one cut per axis')
    vm=vertical[0] if vertical else None;hm=horizontal[0] if horizontal else None
    vc=vm[1] if vm else None;hr=hm[0] if hm else None
    if vm and not any(c==vc for r,c in fg):raise ValueError('Vertical marker must hit foreground')
    if hm and not any(r==hr for r,c in fg):raise ValueError('Horizontal marker must hit foreground')
    fixed={p for p in fg if p[1]==vc or p[0]==hr}
    sectors=[]
    ys=(0,1) if hm else (0 if vm[0]==0 else 1,)
    xs=(0,1) if vm else (0 if hm[1]==0 else 1,)
    for y in ys:
        for x in xs:
            eligible=all_corners or (vm is not None and y==(0 if vm[0]==0 else 1)) or (hm is not None and x==(0 if hm[1]==0 else 1))
            cells={p for p in fg-fixed if (hr is None or (p[0]>hr)==bool(y)) and (vc is None or (p[1]>vc)==bool(x))}
            if cells and eligible:
                for part in (components(cells) if split_components else [cells]):
                    sectors.append({'corner':(y,x),'cells':part,'bbox':bbox(part),'size':len(part)})
    if not sectors:raise ValueError('No nonempty movable sector')
    return {'h':h,'w':w,'fg':fg,'markers':marks,'vertical':vm,'horizontal':hm,'fixed':fixed,'sectors':sectors}

def selected(sectors,value,rival=None):
    mode={'all_sectors':'all','largest_sector':'largest','smallest_sector':'smallest',
          'first_sector':'first','last_sector':'last','bbox_area':'bbox'}.get(rival,value)
    if mode=='all':return sectors
    if mode=='largest':return [max(sectors,key=lambda s:s['size'])]
    if mode=='smallest':return [min(sectors,key=lambda s:s['size'])]
    if mode=='first':return sectors[:1]
    if mode=='last':return sectors[-1:]
    if mode=='bbox':return [max(sectors,key=lambda s:(s['bbox'][2]-s['bbox'][0]+1)*(s['bbox'][3]-s['bbox'][1]+1))]
    raise ValueError('Unknown selection')

def solve(g,value='all',rival=None):
    if value not in VALUES or (rival is not None and rival not in RIVALS):raise ValueError('Unknown rule')
    p=parse(g,all_corners=rival=='all_corners',split_components=rival=='split_components');h,w=p['h'],p['w']
    out=[[1]*w for _ in range(h)]
    for r,c in p['markers']:
        vertical=r in (0,h-1)
        hits=sorted(pr if vertical else pc for pr,pc in p['fg'] if (pc==c if vertical else pr==r))
        positive=(r==0 if vertical else c==0);start=(r if vertical else c)
        last=hits[-1] if positive else hits[0]
        if rival=='first_hit_rays':last=hits[0] if positive else hits[-1]
        if rival=='whole_canvas_rays':last=(h-1 if vertical else w-1) if positive else 0
        if rival=='no_rays':last=start
        for t in range(min(start,last),max(start,last)+1):out[t if vertical else r][c if vertical else t]=2
    for r,c in p['fixed']:out[r][c]=7
    for s in selected(p['sectors'],value,rival):
        r0,c0,r1,c1=bbox(p['fg']) if rival=='global_bbox' else s['bbox'];y,x=s['corner']
        dr=(-r0 if y==0 else h-1-r1);dc=(-c0 if x==0 else w-1-c1)
        if rival=='no_move':dr=dc=0
        for r,c in s['cells']:
            if 0<=r+dr<h and 0<=c+dc<w:out[r+dr][c+dc]=7
    return out

def self_check(g):
    try:parse(g);return []
    except (ValueError,TypeError,IndexError) as e:return [str(e)]

def _rng(seed,tag):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{tag}'.encode()).digest(),'big'))

def _scene(seed,tag,stress=False,single=False):
    rng=_rng(seed,tag);h=30 if stress else rng.randrange(18,28);w=30 if stress else rng.randrange(18,28)
    hr=h//2+rng.randrange(-1,2);vc=w//2+rng.randrange(-1,2)
    g=[[1]*w for _ in range(h)]
    # Rich disconnected masks are interpreted as sectors, not connected objects.
    for y in (0,1):
        for x in (0,1):
            if stress:
                rh=rng.randrange(10,min(12,hr-1 if y==0 else h-hr-2)+1)
                cw=rng.randrange(10,min(12,vc-1 if x==0 else w-vc-2)+1)
                r0=1 if y==0 else h-rh-1
                c0=1 if x==0 else w-cw-1
                density=rng.choice((0.45,0.6,0.75,0.85))
            else:
                rh=rng.randrange(3,6);cw=rng.randrange(3,6)
                r0=hr-rh-rng.randrange(1,3) if y==0 else hr+rng.randrange(1,3)
                c0=vc-cw-rng.randrange(1,3) if x==0 else vc+rng.randrange(1,3)
                density=rng.choice((0.25,0.4,0.65,0.85))
            mask={(r,c) for r in range(rh) for c in range(cw) if rng.random()<density}
            mask.update(((0,0),(rh-1,cw-1)))
            if stress:
                mask.update((r,0) for r in range(rh))
                mask.update((0,c) for c in range(cw))
            # Distinct cells that touch the cut can become detached after cutting.
            for r,c in mask:g[r+r0][c+c0]=7
    for r in (hr-3,hr-1,hr+2,hr+4):g[r][vc]=7
    for c in (vc-4,vc-2,vc+1,vc+3):g[hr][c]=7
    # Sweep all orientations, including parents with a single cut.
    vside=rng.choice((0,h-1));hside=rng.choice((0,w-1))
    if not single or rng.choice((True,False)):g[vside][vc]=2
    if not single or not any(2 in row for row in g):g[hr][hside]=2
    return g

@lru_cache(maxsize=128)
def _bank(seed):
    # Reject only teaching candidates, never use query labels to choose the demos.
    for attempt in range(256):
        demos=[_scene(seed,f'demo:{attempt}:{i}') for i in range(2)]
        okay=True
        for value in VALUES:
            equivalent='all_sectors' if value=='all' else 'largest_sector'
            for rival in RIVALS:
                if rival==equivalent:continue
                if all(solve(g,value,rival)==solve(g,value) for g in demos):okay=False;break
            if not okay:break
        if okay:break
    else:raise RuntimeError('Bounded distinguishing-demo search exhausted')
    demos += [_scene(seed,f'extra:{i}',single=(i%2==0)) for i in range(4)]
    queries=[_scene(seed,f'query:{i}',stress=i==3,single=i in (0,1)) for i in range(4)]
    if len({json.dumps(g) for g in demos+queries})!=10:raise RuntimeError('Input collision')
    return demos,queries

def setting(settings):
    if type(settings) is not dict or set(settings)!={'selection'} or type(settings['selection']) is not str or settings['selection'] not in VALUES:
        raise ValueError('Expected exact selection=all|largest setting')
    return settings['selection']

def program(settings):
    value=setting(settings)
    if value=='all':return (HERE/'canonical.rkt').read_text()
    return _program(value)

def _program(value,rival=None):
    source=(HERE/'canonical.rkt').read_text()
    sm={'all':0,'largest':1}[value]
    sm={'all_sectors':0,'largest_sector':1,'smallest_sector':2,'first_sector':3,'last_sector':4,'bbox_area':5}.get(rival,sm)
    gm={'split_components':1,'global_bbox':2,'no_move':3}.get(rival,0)
    rm={'no_rays':1,'whole_canvas_rays':2,'first_hit_rays':3}.get(rival,0)
    return source.replace('(define selection-mode 0)',f'(define selection-mode {sm})').replace('(define geometry-mode 0)',f'(define geometry-mode {gm})').replace('(define ray-mode 0)',f'(define ray-mode {rm})').replace('(define include-unmarked #f)',f"(define include-unmarked {'#t' if rival=='all_corners' else '#f'})")

def rival_program(settings,rival):
    if rival not in RIVALS:raise ValueError('Unknown rival')
    return _program(setting(settings),rival)

def generate(seed,settings,demos=3,queries=4):
    integer(seed,0,2**63-1,'seed');integer(demos,2,6,'demos');integer(queries,1,4,'queries');value=setting(settings)
    ds,qs=copy.deepcopy(_bank(seed))
    label=lambda grid:{'input':grid,'output':solve(grid,value)}
    return {'train':[label(g) for g in ds[:demos]],'test':[label(g) for g in qs[:queries]],'program_solution':program(settings)}

def present(seed,settings,demos=3,queries=4,presentation_seed=0):
    integer(queries,1,4,'queries');integer(presentation_seed,0,2**63-1,'presentation_seed')
    ep=generate(seed,settings,demos,4);order=list(range(4));_rng(seed,f'presentation:{presentation_seed}').shuffle(order)
    return {'public':[{'train':copy.deepcopy(ep['train']),'test':[{'input':copy.deepcopy(ep['test'][i]['input'])}]} for i in order[:queries]],
            'private':{'settings':copy.deepcopy(settings),'seed':seed,'presentation_seed':presentation_seed,'source_indices':order,
                       'source_pairs':ep['test'],'program':ep['program_solution']}}

def intermediate(g,settings):
    value=setting(settings);p=parse(g)
    return {'sectors':[{'corner':list(s['corner']),'size':s['size'],'bbox':list(s['bbox'])} for s in p['sectors']],
            'selected_corners':[list(s['corner']) for s in selected(p['sectors'],value)]}

def counterfactual_program(settings):return rival_program(settings,'smallest_sector')

def dependency():
    return {'step_a':'Trace edge-marker cuts, partition off-cut foreground into eligible corner sectors, and rank sectors by occupied-cell count.',
            'intermediate':'Selected sector identity, its foreground coordinates, occupied-cell count and bounding box.',
            'step_b':'Translate only the selected sector to its associated canvas corner while retaining cut pixels and marker rays.',
            'why_b_depends_on_a':'The selected mask and docking translation depend on the input-derived cut partition and area ranking; the smallest-sector substitution changes the final moved shape.'}
