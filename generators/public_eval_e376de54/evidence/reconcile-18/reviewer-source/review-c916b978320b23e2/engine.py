"""Central-segment translation normalization and a matched-input sequential family."""
from __future__ import annotations
from collections import Counter, deque
import hashlib
import random

SETTINGS=('normalize_only','highlight_largest_adjustment')
DIRS=((0,1),(1,0),(1,1),(1,-1))
N8=tuple((dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc)


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}; bool is forbidden')
    return value


def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list
        or not 1<=len(g[0])<=30 or any(type(row) is not list or len(row)!=len(g[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular 1..30 exact-integer color grid')


def _background(g):
    counts=Counter(v for row in g for v in row); top=max(counts.values())
    winners=[v for v,n in counts.items() if n==top]
    if len(winners)!=1: raise ValueError('Expected a unique modal background')
    return winners[0]


def _components(g,bg):
    h,w=len(g),len(g[0]); seen=set(); out=[]
    for r in range(h):
        for c in range(w):
            color=g[r][c]
            if color==bg or (r,c) in seen: continue
            q=deque([(r,c)]); seen.add((r,c)); cells=[]
            while q:
                p=q.popleft(); cells.append(p)
                for dr,dc in N8:
                    x,y=p[0]+dr,p[1]+dc
                    if 0<=x<h and 0<=y<w and (x,y) not in seen and g[x][y]==color:
                        seen.add((x,y));q.append((x,y))
            out.append({'id':len(out),'color':color,'cells':sorted(cells)})
    return out


def _direction(cells):
    rs={r for r,c in cells};cs={c for r,c in cells}
    if len(rs)==1: d=(0,1)
    elif len(cs)==1: d=(1,0)
    elif len({r-c for r,c in cells})==1:d=(1,1)
    elif len({r+c for r,c in cells})==1:d=(1,-1)
    else:raise ValueError('Every foreground object must be a straight axis/diagonal segment')
    anchor=min(cells)
    expected={(anchor[0]+i*d[0],anchor[1]+i*d[1]) for i in range(len(cells))}
    if set(cells)!=expected:raise ValueError('Segments must be contiguous and lead from their top/left endpoint')
    return d,anchor


def _offset(obj,d):
    r,c=obj['anchor']
    return r if d==(0,1) else c if d==(1,0) else r-c if d==(1,1) else r+c


def _shift(delta,d):
    if d==(0,1):return (delta,0)
    if d==(1,0):return (0,delta)
    if delta%2:raise ValueError('Diagonal lane offsets must have even parity')
    k=delta//2
    return (k,-k) if d==(1,1) else (k,k)


def _normalized_cells(obj,target_length):
    """Wrong-rule helper: resize from each object's own leading endpoint."""
    r,c=obj['anchor'];dr,dc=obj['direction']
    return [(r+i*dr,c+i*dc) for i in range(target_length)]


def analyze(g):
    grid_check(g);bg=_background(g);objs=_components(g,bg)
    if len(objs)<3 or len(objs)%2==0:raise ValueError('Expected an odd collection of at least three segments')
    dirs=[]
    for obj in objs:
        d,a=_direction(obj['cells']);obj['direction']=d;obj['anchor']=a;obj['length']=len(obj['cells']);dirs.append(d)
    if len(set(dirs))!=1:raise ValueError('All segments must be parallel')
    d=dirs[0];ordered=sorted(objs,key=lambda o:(_offset(o,d),o['anchor']))
    central=ordered[len(ordered)//2];base=set(central['cells'])
    for obj in objs:
        dr,dc=_shift(_offset(obj,d)-_offset(central,d),d)
        obj['target_cells']=sorted((r+dr,c+dc) for r,c in base)
        if any(not (0<=r<len(g) and 0<=c<len(g[0])) for r,c in obj['target_cells']):
            raise ValueError('Translated central template leaves the canvas')
        obj['adjustment']=len(set(obj['cells'])^set(obj['target_cells']))
    max_adjust=max(o['adjustment'] for o in objs);max_original=max(o['length'] for o in objs)
    return {'height':len(g),'width':len(g[0]),'background':bg,'direction':d,
            'target_length':central['length'],'central_id':central['id'],'objects':objs,
            'largest_adjustment_ids':[o['id'] for o in objs if o['adjustment']==max_adjust],
            'largest_original_ids':[o['id'] for o in objs if o['length']==max_original]}


def solve(g,finish='normalize_only',rival=None):
    if finish not in SETTINGS:raise ValueError('Unknown finish setting')
    if rival is not None and rival not in set(rivals(finish)):raise ValueError('Unknown rival')
    if rival=='identity':
        grid_check(g)
        return [row[:] for row in g]
    if rival=='other_setting':finish=SETTINGS[1-SETTINGS.index(finish)];rival=None
    info=analyze(g);out=[row[:] for row in g]
    for obj in info['objects']:
        for r,c in obj['cells']:out[r][c]=info['background']
    template=info['objects'][info['central_id']]['cells']
    ordered=sorted(info['objects'],key=lambda o:(_offset(o,info['direction']),o['anchor']))
    source=ordered[0] if rival=='copy_first' else ordered[-1] if rival=='copy_last' else None
    for obj in info['objects']:
        cells=obj['target_cells']
        if source is not None:
            delta=_offset(obj,info['direction'])-_offset(source,info['direction'])
            dr,dc=_shift(delta,info['direction']);cells=[(r+dr,c+dc) for r,c in source['cells']]
        elif rival=='resize_in_place':cells=_normalized_cells(obj,info['target_length'])
        color=obj['color']
        if finish=='highlight_largest_adjustment':
            selected=(info['largest_original_ids'] if rival=='largest_original_highlight' else
                      [min(info['objects'],key=lambda o:o['length'])['id']] if rival=='smallest_original_highlight' else
                      [ordered[0]['id']] if rival=='first_segment_highlight' else info['largest_adjustment_ids'])
            if obj['id'] in selected:color=9
        for r,c in cells:
            if 0<=r<info['height'] and 0<=c<info['width']:out[r][c]=color
    return out


def rivals(finish):
    if finish=='normalize_only':
        return ('other_setting','identity','copy_first','copy_last','resize_in_place')
    if finish=='highlight_largest_adjustment':
        return ('other_setting','largest_original_highlight','smallest_original_highlight','first_segment_highlight')
    raise ValueError('Unknown finish setting')


def rival_output(g,finish,name):
    if name=='identity':return [row[:] for row in g]
    return solve(g,finish,rival=name)


def _rng(seed,kind,index):
    integer(seed,0,2**63-1,'seed');integer(index,0,5 if kind=='demo' else 3,'index')
    return random.Random(int.from_bytes(hashlib.sha256(f'e376de54:v2:{seed}:{kind}:{index}'.encode()).digest(),'big'))


def _dimensions(kind,index):
    return ((16,16),(18,20),(21,18),(20,24),(24,22),(26,28))[index] if kind=='demo' else ((18,22),(22,19),(26,25),(30,30))[index]


def _candidate_anchors(h,w,d,span):
    if d==(0,1):return [(r,c) for r in range(1,h-1) for c in range(1,w-span)]
    if d==(1,0):return [(r,c) for r in range(1,h-span) for c in range(1,w-1)]
    if d==(1,1):return [(r,c) for r in range(1,h-span) for c in range(1,w-span)]
    return [(r,c) for r in range(1,h-span) for c in range(span,w-1)]


def _cells(anchor,d,n):
    return {(anchor[0]+i*d[0],anchor[1]+i*d[1]) for i in range(n)}


def scene(seed,kind,index):
    """Construct a lawful scene without retries or silent fallback.

    The direction schedule guarantees support for all four canonical orientations.
    Diagonal scenes use adjacent parity-compatible lanes; axis-aligned scenes use
    two-cell lane gaps.  A finite exhaustive anchor search proves placement or
    raises rather than weakening the requested profile.
    """
    if kind not in ('demo','query'):raise ValueError('kind must be demo or query')
    rng=_rng(seed,kind,index);h,w=_dimensions(kind,index)
    if rng.randrange(2) and h!=w:h,w=w,h
    bg=rng.choice((0,1,7,8));palette=[c for c in range(10) if c not in (bg,9)]
    rng.shuffle(palette)
    schedule=(DIRS if kind=='demo' else (DIRS[3],DIRS[0],DIRS[1],DIRS[2]))
    preferred=schedule[index%len(schedule)]
    directions=(preferred,)+tuple(d for d in DIRS if d!=preferred)
    count=7 if kind=='query' and index==3 else 5;m=count//2
    chosen=None
    chosen_direction=None
    chosen_target=None
    # Small canvases need shorter diagonal templates; larger cases retain 6--8.
    preferred_target=6 + ((seed+index+(0 if kind=='demo' else 1))%2)
    if max(h,w)>=24: preferred_target=6+((seed+index)%3)
    target_options=tuple(dict.fromkeys((preferred_target,6,7,8)))
    for d in directions:
        perp=(1,0) if d==(0,1) else (0,1) if d==(1,0) else (1,-1) if d==(1,1) else (1,1)
        gap=2 if d in ((0,1),(1,0)) else 1
        for target in target_options:
            if target<6:continue
            if count==5:
                lengths=[target-4,target-1,target,target+2,target+1];starts=[0,3,0,0,-1]
            else:
                lengths=[target-4,target-1,target-1,target,target+2,target+1,target-1];starts=[0,3,-1,0,0,-1,1]
            if min(lengths)<1:continue
            candidates=[(r,c) for r in range(h) for c in range(w)];rng.shuffle(candidates)
            for base in candidates:
                records=[];all_cells=[];ok=True
                for pos,(n,shift) in enumerate(zip(lengths,starts)):
                    lane=pos-m
                    ta=(base[0]+lane*gap*perp[0],base[1]+lane*gap*perp[1])
                    oa=(ta[0]+shift*d[0],ta[1]+shift*d[1])
                    target_cells=_cells(ta,d,target);orig=_cells(oa,d,n)
                    if any(not (0<=r<h and 0<=c<w) for r,c in target_cells|orig):ok=False;break
                    records.append((orig,target_cells));all_cells.append(orig)
                if ok and len(set().union(*all_cells))==sum(map(len,all_cells)):
                    chosen=records;chosen_direction=d;chosen_target=target;break
            if chosen is not None:break
        if chosen is not None:break
    if chosen is None:raise RuntimeError('constructive aligned-line placement failed')
    g=[[bg]*w for _ in range(h)]
    for i,(orig,_) in enumerate(chosen):
        for r,c in orig:g[r][c]=palette[i]
    info=analyze(g)
    if info['direction']!=chosen_direction or info['target_length']!=chosen_target:
        raise RuntimeError('constructed scene failed its declared profile')
    return g

def generate(seed,kind,index):return scene(seed,kind,index)


def self_check(g):
    try:analyze(g)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []
