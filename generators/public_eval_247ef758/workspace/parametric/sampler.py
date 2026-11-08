"""Standalone matched-border template-placement input sampler.

The ordinary generate API returns inputs only. Python predictions support native
claims and explicit rival auditing; protected Racket is the label authority.
"""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import hashlib
import random

GENERATOR_ID='public_eval_247ef758'
TASK_ID=GENERATOR_ID
RULE_TASK_ID='ee_247ef758'
VERSION='1.0.0'
SUMMARY='Match opposite frame markers and center each source template on all crossings.'
EXAMPLES_NEEDED=2
MIN_STRICT_FRAC=1.0
RIVALS=('other_setting','color_ascending','color_descending','bbox_priority','reverse_source',
        'smallest_first','small_bbox_priority','erase_unmatched','keep_sources','top_left_markers','either_edge_markers',
        'zip_crossings','first_crossing','centroid_anchor','filled_template','overwrite_later','corner_anchor')

def validate_grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or any(type(r) is not list for r in g)
        or not 1<=len(g[0])<=30 or any(len(r)!=len(g[0]) for r in g)
        or any(type(v) is not int or not 0<=v<=9 for r in g for v in r)):
        raise ValueError('expected rectangular integer-color grid')

def records(g,markers='both'):
    validate_grid(g);h,w=len(g),len(g[0])
    candidates=[c for c in range(w) if g[0][c]!=0 and len({row[c] for row in g})==1]
    if not candidates:raise ValueError('missing uniform separator')
    sep=candidates[0];left=sep+1
    if not 0<sep<left<w-1:raise ValueError('invalid palette/frame layout')
    colors=list(dict.fromkeys(g[r][c] for r in range(h) for c in range(sep) if g[r][c]))
    parts=[]
    for co in colors:
        pts=[(r,c) for r in range(h) for c in range(sep) if g[r][c]==co]
        r0=min(r for r,c in pts);r1=max(r for r,c in pts);c0=min(c for r,c in pts);c1=max(c for r,c in pts)
        def match(a,b):
            return (a==co or b==co) if markers=='either' else a==co if markers=='top_left' else a==b==co
        rs=[r for r in range(1,h-1) if match(g[r][left],g[r][-1])]
        cs=[c for c in range(left+1,w-1) if match(g[0][c],g[-1][c])]
        parts.append(dict(color=co,cells=pts,box=[r0,c0,r1,c1],anchor=[(r0+r1)//2,(c0+c1)//2],rows=rs,cols=cs,area=len(pts),bbox_area=(r1-r0+1)*(c1-c0+1)))
    return sep,parts

def predict(g,mode='source_order',rival=None):
    if mode not in ('source_order','largest_first'):raise ValueError('unknown priority')
    if rival is not None and rival not in RIVALS:raise ValueError('unknown rival')
    if rival=='other_setting':mode='largest_first' if mode=='source_order' else 'source_order'
    sep,parts=records(g,'top_left' if rival=='top_left_markers' else 'either' if rival=='either_edge_markers' else 'both')
    matched=[p for p in parts if p['rows'] and p['cols']]
    order=sorted(matched,key=lambda p:-p['area']) if mode=='largest_first' else matched[:]
    if rival=='color_ascending':order=sorted(matched,key=lambda p:p['color'])
    if rival=='color_descending':order=sorted(matched,key=lambda p:-p['color'])
    if rival=='bbox_priority':order=sorted(matched,key=lambda p:-p['bbox_area'])
    if rival=='small_bbox_priority':order=sorted(matched,key=lambda p:p['bbox_area'])
    if rival=='reverse_source':order=matched[::-1]
    if rival=='smallest_first':order=sorted(matched,key=lambda p:p['area'])
    out=[row[:] for row in g]
    if rival!='keep_sources':
        for p in (parts if rival=='erase_unmatched' else matched):
            for r,c in p['cells']:out[r][c]=0
    for p in order:
        pts=p['cells'];ar,ac=p['anchor']
        if rival=='centroid_anchor':ar=sum(r for r,c in pts)//len(pts);ac=sum(c for r,c in pts)//len(pts)
        if rival=='corner_anchor':ar,ac=p['box'][:2]
        if rival=='filled_template':
            r0,c0,r1,c1=p['box'];pts=[(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)]
        targets=[(r,c) for r in p['rows'] for c in p['cols']]
        if rival=='zip_crossings':targets=list(zip(p['rows'],p['cols']))
        if rival=='first_crossing':targets=targets[:1]
        for rr,cc in targets:
            for r,c in pts:
                r,c=rr+r-ar,cc+c-ac
                if (0<=r<len(g) and sep+1<=c<len(g[0]) and
                    (out[r][c]==0 or (rival=='overwrite_later' and g[r][c]==0))):out[r][c]=p['color']
    return out

def sample(seed,index):
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('invalid seed')
    if type(index) is not int or index<0:raise ValueError('invalid sample index')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'{TASK_ID}:{seed}:{index}'.encode()).digest(),'big'))
    if 100<=index<=103:h,w=[(14,18),(18,23),(24,27),(30,30)][index-100]
    else:h,w=rng.choice([(14,18),(16,21),(19,24),(23,27)])
    sep=rng.randint(5,min(7,w-12));left=sep+1
    separator,border=rng.sample(range(1,10),2)
    a,b,c,d,e=rng.sample([x for x in range(1,10) if x not in (separator,border)],5)
    # Choose one coherent diagonal, preserving five-by-five extents.
    sparse={(i,i) for i in range(5)} if rng.randrange(2)==0 else {(i,4-i) for i in range(5)}
    dense={(r,c) for r in range(3) for c in range(3)}
    variant=rng.randrange(5)
    if variant in (1,2):dense.remove((1,1))
    if variant==2:dense.remove(rng.choice([(0,0),(0,2),(2,0),(2,2)]))
    if variant==3:dense={(0,1),(1,0),(1,1),(1,2),(2,1)}
    if variant==4:dense={(0,0),(1,0),(1,1),(2,2)}
    bar={(0,i) for i in range(rng.randint(2,5))}
    entries=[(a,sparse),(b,dense),(c,bar),(d,{(0,0),(0,1)})]
    rng.shuffle(entries)
    total=sum(max(r for r,c in pts)+1 for co,pts in entries)+len(entries)-1
    extra=h-total
    gaps=[0]*len(entries)
    for _ in range(extra):gaps[rng.randrange(len(gaps))]+=1
    grid=[[0]*w for _ in range(h)]
    for r in range(h):grid[r][sep]=separator;grid[r][left]=grid[r][-1]=border
    for cc in range(left,w):grid[0][cc]=grid[-1][cc]=border
    row=0
    for j,(co,pts) in enumerate(entries):
        row+=gaps[j];sw=max(c for r,c in pts)+1;col=rng.randrange(sep-sw+1)
        for r,cc in pts:grid[row+r][col+cc]=co
        row+=max(r for r,c in pts)+2
    if index==103:
        rows={a:[3,13,24],b:[4,14,25],c:[8,18,19,28]}
        cols={a:[left+3,left+9,w-4],b:[left+4,left+10,w-3],c:[left+6,left+12,w-7]}
    else:
        rows={a:[3,h-4],b:[4,h-3],c:[2,5]}
        # Distinct paired marker coordinates. Multiple matches force products.
        cols={a:[left+2,w-4],b:[left+3,w-3],c:[left+1,left+4]}
    for co in (a,b,c):
        for r in rows[co]:grid[r][left]=grid[r][-1]=co
        for cc in cols[co]:grid[0][cc]=grid[-1][cc]=co
    free_r=[r for r in range(1,h-1) if grid[r][left]==border]
    free_c=[cc for cc in range(left+1,w-1) if grid[0][cc]==border]
    # Decoy has paired columns but mismatched rows: it must stay at source.
    rd=rng.choice(free_r);free_r.remove(rd);cd=rng.choice(free_c);free_c.remove(cd)
    grid[rd][left]=d;grid[rd][-1]=e;grid[0][cd]=grid[-1][cd]=d
    # A one-edge extra crossing for a real source must also be ignored.
    rx=rng.choice(free_r);grid[rx][left]=a;grid[rx][-1]=e
    cx=rng.choice(free_c);grid[0][cx]=a;grid[-1][cx]=e
    return grid

@lru_cache(maxsize=128)
def teaching_seed(seed):
    """Bounded demonstrations-only filtering; never inspects query inputs/labels."""
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('invalid seed')
    for attempt in range(128):
        draw=int.from_bytes(hashlib.sha256(f'{seed}:teaching:{attempt}'.encode()).digest(),'big')%(2**63)
        grids=[sample(draw,i) for i in (0,1)]
        adequate=True
        for mode in ('source_order','largest_first'):
            labels=[predict(g,mode) for g in grids]
            for name in RIVALS:
                if all(predict(g,mode,name)==label for g,label in zip(grids,labels)):
                    adequate=False;break
            if not adequate:break
        if adequate:return draw,attempt
    raise RuntimeError('128 bounded demos-only teaching attempts exhausted')

def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if overrides:raise ValueError('this sampler exposes no override axes')
    return sample(seed,sample_index)

def self_check(grid,**_):
    try:
        sep,parts=records(grid)
        if not any(p['rows'] and p['cols'] for p in parts):return ['need a matched template']
    except (ValueError,TypeError) as exc:return [str(exc)]
    return []
