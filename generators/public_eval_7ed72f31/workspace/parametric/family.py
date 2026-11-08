"""Marker-relative reflection/half-turn family, with repeated-color local groups."""
from __future__ import annotations
import copy
import hashlib
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from puzzle_generators.base import gen_ctx

TASK='public_eval_7ed72f31'
VERSION='1.0.0'
MODES=('reflect','half_turn')
RIVALS=('identity','always_half_turn','always_axis_reflect','line_only','point_only',
        'segment_clip','four_connected','first_group_only','largest_group_only',
        'source_bbox_center','near_only','same_color_global')
BASE=Path(__file__).resolve().parent
DEPENDENCY={
 'step_a':'Recover the background, eight-connected marker/source groups, each red marker bounding box and its source-colored cells.',
 'intermediate':'Per-group marker geometry (point, horizontal or vertical), doubled midpoint coordinates and source-colored cell offsets.',
 'step_b':'Consume those records to copy each source by its marker axis or, for half_turn, by the marker midpoint.',
 'why_b_depends_on_a':'The destination of every copied pixel depends on its own marker location and geometry, not on its color or source bounding box.'}


def _integer(x,lo,hi,name):
    if type(x) is not int or not lo<=x<=hi: raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return x


def validate_grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
        or any(type(row) is not list or len(row)!=len(g[0]) or
               any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected rectangular 1..30 exact-integer color grid')
    return g


def background(g):
    counts=Counter(v for row in g for v in row)
    return min(counts,key=lambda v:(-counts[v],v))


def _components(g,bg,eight=True):
    remaining={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg}
    groups=[]
    deltas=[(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr or dc) and (eight or abs(dr)+abs(dc)==1)]
    while remaining:
        first=min(remaining); remaining.remove(first); stack=[first]; cells=[first]
        while stack:
            r,c=stack.pop()
            for dr,dc in deltas:
                point=(r+dr,c+dc)
                if point in remaining:
                    remaining.remove(point); stack.append(point); cells.append(point)
        groups.append(sorted(cells))
    return groups


def analyze(g,eight=True):
    validate_grid(g); bg=background(g)
    if bg==2: raise ValueError('Red cannot be the background')
    result=[]
    for cells in _components(g,bg,eight):
        red=[p for p in cells if g[p[0]][p[1]]==2]
        source=[(r,c,g[r][c]) for r,c in cells if g[r][c]!=2]
        if not red or not source: continue
        r0=min(r for r,c in red); r1=max(r for r,c in red)
        c0=min(c for r,c in red); c1=max(c for r,c in red)
        if len(red)==1: kind='point'
        elif r0==r1 and len(red)==c1-c0+1: kind='horizontal'
        elif c0==c1 and len(red)==r1-r0+1: kind='vertical'
        else: raise ValueError('A marker must be a singleton or a complete straight line')
        result.append({'kind':kind,'marker_bbox':[r0,c0,r1,c1],
                       'doubled_center':[r0+r1,c0+c1], 'marker':red,'source':source})
    if not result and eight: raise ValueError('No marker-attached source group found')
    return result


def destination(group,r,c,mode):
    r0,c0,r1,c1=group['marker_bbox']
    if mode=='half_turn' or group['kind']=='point': return r0+r1-r,c0+c1-c
    return (2*r0-r,c) if group['kind']=='horizontal' else (r,2*c0-c)


def _render(g,groups,mode,rival=None):
    out=copy.deepcopy(g); bg=background(g); h,w=len(g),len(g[0])
    for group in groups:
        r0,c0,r1,c1=group['marker_bbox']; source=group['source']
        if rival=='same_color_global':
            colors={v for r,c,v in source}
            source=[(r,c,v) for r,row in enumerate(g) for c,v in enumerate(row) if v in colors]
        for r,c,v in source:
            if rival=='near_only' and min(max(abs(r-rr),abs(c-cc)) for rr,cc in group['marker'])>2: continue
            rr,cc=destination(group,r,c,mode)
            if rival=='always_axis_reflect' and group['kind']=='point': rr,cc=2*r0-r,c
            if rival=='source_bbox_center':
                rr=min(x[0] for x in source)+max(x[0] for x in source)-r
                cc=min(x[1] for x in source)+max(x[1] for x in source)-c
            if rival=='segment_clip' and group['kind']!='point':
                if group['kind']=='horizontal' and not c0<=cc<=c1: continue
                if group['kind']=='vertical' and not r0<=rr<=r1: continue
            if 0<=rr<h and 0<=cc<w and g[rr][cc]==bg: out[rr][cc]=v
    return out


def solve(g,mode='reflect'):
    if mode not in MODES: raise ValueError('Undeclared line action')
    return _render(g,analyze(g),mode)


def rival_solve(g,mode,rival):
    if rival not in RIVALS: raise ValueError('Unknown rival')
    if rival=='identity': return copy.deepcopy(g)
    groups=analyze(g,eight=(rival!='four_connected'))
    if rival=='always_half_turn': mode='half_turn'
    if rival=='always_axis_reflect': mode='reflect'
    if rival=='line_only': groups=[x for x in groups if x['kind']!='point']
    if rival=='point_only': groups=[x for x in groups if x['kind']=='point']
    if rival=='first_group_only': groups=groups[:1]
    if rival=='largest_group_only': groups=[max(groups,key=lambda x:len(x['source']))]
    return _render(g,groups,mode,rival)


def _settings(settings):
    if type(settings) is not dict or set(settings)!={'line_action'} or settings['line_action'] not in MODES:
        raise ValueError('Expected exactly line_action=reflect or half_turn')
    return settings['line_action']


def program(settings):
    mode=_settings(settings)
    return (BASE/('canonical.rkt' if mode=='reflect' else 'half_turn.rkt')).read_text()


def _rot(p,size,k):
    r,c=p
    for _ in range(k): r,c=c,size-1-r
    return r,c


@lru_cache(maxsize=4096)
def _sample_frozen(seed,index,stress):
    ctx=gen_ctx(seed=seed,sample_index=index,version=VERSION,task_id=TASK)
    rng=ctx.draw_rng('marker_geometry_and_local_sources')
    for attempt in range(256):
        tile=10 if stress else rng.randint(9,12)
        side=3 if stress else 2
        size=side*tile
        bg=rng.choice([x for x in range(10) if x!=2])
        palette=rng.sample([x for x in range(10) if x not in (bg,2)],3)
        g=[[bg]*size for _ in range(size)]
        # A horizontal marker and a point share a color and tile row, exposing
        # the invalid rule that globally associates all cells of that color.
        places=[(0,0,'horizontal'),(0,1,'point'),(1,0,'vertical')]
        if stress:
            places += [(r,c,('point','horizontal','vertical')[(r+c+index)%3])
                       for r in range(3) for c in range(3) if (r,c) not in {(0,0),(0,1),(1,0)}]
        elif index%2: places.append((1,1,rng.choice(('point','horizontal','vertical'))))
        intended=[]
        for j,(tr,tc,kind) in enumerate(places):
            color=palette[0] if j<2 else palette[1+(j%2)]
            if kind=='point':
                red=[(4,4)]
                src={(3,3),(2,2),(1,1),(1,2),(2,1),(3,2)}
                for r in range(1,4):
                    for c in range(1,4):
                        if rng.random()<.3: src.add((r,c))
                k=rng.randrange(4)
            else:
                length=rng.choice((2,3,4,5)); start=3 if length<4 else 2
                red=[(4,c) for c in range(start,start+length)]
                src={(3,start-1),(2,start-2),(1,start-2),(2,start-1),
                     (3,start),(1,start-1),(0,start-1)}
                for r in range(1,4):
                    for c in range(start-1,start+1):
                        if rng.random()<.45: src.add((r,c))
                k=rng.choice((0,2)) if kind=='horizontal' else rng.choice((1,3))
            dr=rng.randrange(tile-8); dc=rng.randrange(tile-8)
            reds=[(tr*tile+dr+r,tc*tile+dc+c) for r,c in [_rot(p,9,k) for p in red]]
            sources=[(tr*tile+dr+r,tc*tile+dc+c,color) for r,c in [_rot(p,9,k) for p in sorted(src)]]
            for r,c in reds: g[r][c]=2
            for r,c,v in sources: g[r][c]=v
            intended.append((reds,sources))
        try:
            groups=analyze(g)
        except ValueError: continue
        if len(groups)!=len(places): continue
        # No input merging or cross-object collisions, under either parameter.
        valid=True
        for mode in MODES:
            destinations={}
            for group in groups:
                for r,c,v in group['source']:
                    rr,cc=destination(group,r,c,mode)
                    if not(0<=rr<size and 0<=cc<size) or g[rr][cc]!=bg:
                        valid=False; break
                    if (rr,cc) in destinations and destinations[rr,cc]!=v:
                        valid=False; break
                    destinations[rr,cc]=v
                if not valid: break
            if not valid: break
        if not valid: continue
        # Randomize global placement/orientation without changing local roles.
        for _ in range(rng.randrange(4)): g=[list(row) for row in zip(*g[::-1])]
        # Expose the local-group rule even with repeated source colors.
        if any(rival_solve(g,m,'same_color_global')==solve(g,m) for m in MODES): continue
        if solve(g,'reflect')==solve(g,'half_turn'): continue
        return tuple(tuple(row) for row in g)
    raise RuntimeError('No collision-free marker scene in 256 bounded attempts')


def sample(seed,index,stress=False):
    _integer(seed,0,2**63-1,'seed'); _integer(index,0,2**31-1,'index')
    if type(stress) is not bool: raise ValueError('stress must be boolean')
    return [list(row) for row in _sample_frozen(seed,index,stress)]


def generate(seed,settings,demos,queries):
    _integer(seed,0,2**63-1,'seed'); _integer(demos,2,6,'demos'); _integer(queries,1,4,'queries')
    mode=_settings(settings)
    ins=[sample(seed,i) for i in range(demos)]
    tests=[sample(seed,100+i,stress=(i==3)) for i in range(queries)]
    if len({json.dumps(g) for g in ins+tests})!=len(ins)+len(tests): raise RuntimeError('Duplicate generated input')
    return {'train':[{'input':g,'output':solve(g,mode)} for g in ins],
            'test':[{'input':g,'output':solve(g,mode)} for g in tests],
            'program_solution':program(settings)}


def public_turn(episode,turn,presentation_seed):
    _integer(turn,0,3,'turn'); _integer(presentation_seed,0,2**63-1,'presentation_seed')
    if len(episode['test'])!=4: raise ValueError('Present from the complete four-query bank')
    order=sorted(range(4),key=lambda i:hashlib.sha256(f'{presentation_seed}:{i}'.encode()).digest())
    return {'train':[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':copy.deepcopy(episode['test'][order[turn]]['input'])}]}
