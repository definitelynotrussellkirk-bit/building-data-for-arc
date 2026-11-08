"""Public 58f5dbd5: associate stencils by color, then carve plate interiors.

Standalone base sampler: standard library and shared GenCtx only. No filesystem
reads or adjacent workspace imports during generation. Geometry and Python label
claims live here; Racket remains the label authority via the native adapter.
"""
from __future__ import annotations
from collections import Counter
import copy
from puzzle_generators.base import gen_ctx
TASK_ID=GENERATOR_ID='public_eval_58f5dbd5'
RULE_TASK_ID='ee_58f5dbd5'
VERSION='1.0.1'
EXAMPLES_NEEDED=2
SUMMARY='Public 58f5dbd5: associate stencils by color, then carve plate interiors.'
AXES={}
MODES=('cutout','emboss')

def _int(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value

def _bbox(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)

def analyse(grid):
    if type(grid) is not list or not 1<=len(grid)<=30 or not grid or type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('grid dimensions must be 1..30')
    H,W=len(grid),len(grid[0])
    if any(type(row) is not list or len(row)!=W or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('grid must be rectangular with integer colors')
    bg=Counter(v for row in grid for v in row).most_common(1)[0][0]
    seen=set();plates=[]
    for r in range(H):
        for c in range(W):
            if grid[r][c]==bg or (r,c) in seen:continue
            color=grid[r][c];component={(r,c)};seen.add((r,c));stack=[(r,c)]
            while stack:
                rr,cc=stack.pop()
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    q=(rr+dr,cc+dc)
                    if 0<=q[0]<H and 0<=q[1]<W and q not in seen and grid[q[0]][q[1]]==color:
                        seen.add(q);component.add(q);stack.append(q)
            r0,c0,r1,c1=_bbox(component)
            if r1-r0+1>=4 and c1-c0+1>=4 and len(component)==(r1-r0+1)*(c1-c0+1):
                raw=[(y,x) for y in range(H) for x in range(W) if grid[y][x]==color and (y,x) not in component]
                if not raw:raise ValueError('plate has no same-color stencil')
                y0,x0,y1,x1=_bbox(raw)
                if y1-y0+1!=r1-r0-1 or x1-x0+1!=c1-c0-1:raise ValueError('stencil dimensions do not match plate interior')
                plates.append(dict(color=color,box=(r0,c0,r1,c1),mask={(y-y0,x-x0) for y,x in raw},source=(y0,x0,y1,x1)))
    if not plates:raise ValueError('no plates')
    if len({p['color'] for p in plates})!=len(plates):raise ValueError('plate colors must be unique')
    bounds=(min(p['box'][0] for p in plates)-1,min(p['box'][1] for p in plates)-1,max(p['box'][2] for p in plates)+1,max(p['box'][3] for p in plates)+1)
    if bounds[0]<0 or bounds[1]<0 or bounds[2]>=H or bounds[3]>=W:raise ValueError('plate layout needs background margin')
    return bg,plates,bounds

def solve(grid,mode='cutout',foil=None):
    if mode not in MODES:raise ValueError('unknown stencil mode')
    bg,plates,bounds=analyse(grid);out=copy.deepcopy(grid)
    for i,p in enumerate(plates):
        r0,c0,r1,c1=p['box'];mh,mw=r1-r0-1,c1-c0-1;mask=p['mask']
        if foil=='flip_lr':mask={(r,mw-1-c) for r,c in mask}
        elif foil=='flip_ud':mask={(mh-1-r,c) for r,c in mask}
        elif foil=='rotate_180':mask={(mh-1-r,mw-1-c) for r,c in mask}
        elif foil=='next_color':mask=plates[(i+1)%len(plates)]['mask']
        elif foil=='solid_interior':mask={(r,c) for r in range(mh) for c in range(mw)}
        elif foil=='empty_interior':mask=set()
        elif foil=='source_order':mask=sorted(plates,key=lambda x:x['source']) [i]['mask']
        elif foil=='numeric_order':mask=sorted(plates,key=lambda x:x['color'])[i]['mask']
        for rr in range(mh):
            for cc in range(mw):
                inside=(rr,cc) in mask
                out[r0+1+rr][c0+1+cc]=p['color'] if (inside==(mode=='emboss')) else bg
    r0,c0,r1,c1=bounds
    return [row[c0:c1+1] for row in out[r0:r1+1]]

def sample(seed,index):
    _int(seed,0,2**63-1,'seed');_int(index,0,2**31-1,'sample_index')
    ctx=gen_ctx(seed=seed,sample_index=index,version='1.0',task_id=TASK_ID)
    rng=ctx.draw_rng('geometry_palette_stencils')
    profile=index%4
    nr,nc,mh,mw=((2,2,3,3),(1,3,3,3),(3,1,4,3),(3,2,3,3))[profile]
    ah,aw=nr*(mh+3)+1,nc*(mw+3)+1
    count=nr*nc;extras=2 if profile!=1 else 1
    # A separate stencil rack is permuted, then the complete canvas transformed.
    cols=1 if profile==1 else 2
    ph=((count+extras+cols-1)//cols)*(mh+1)+1;pw=cols*(mw+1)+1
    W=aw+pw+1;H=max(ah,ph)+2
    if profile==3:H=W=30
    else:
        H=min(30,H+rng.randrange(2,5));W=min(30,W+rng.randrange(0,3))
    bg=rng.randrange(10);palette=rng.sample([c for c in range(10) if c!=bg],count+extras)
    grid=[[bg]*W for _ in range(H)]
    ar=0 if profile==3 else rng.randrange(H-ah+1)
    ac=0
    sy=H-ph if profile==3 else rng.randrange(H-ph+1)
    sx=W-pw
    masks=[]
    for k in range(count+extras):
        for attempt in range(4096):
            m={(r,c) for r in range(mh) for c in range(mw) if rng.random()<.5}
            if not 2<=len(m)<mh*mw:continue
            if _bbox(m)!=(0,0,mh-1,mw-1):continue
            if m=={(r,mw-1-c) for r,c in m} or m=={(mh-1-r,c) for r,c in m} or m=={(mh-1-r,mw-1-c) for r,c in m}:continue
            if m not in masks:break
        else:raise ValueError('bounded stencil sampling exhausted')
        masks.append(m)
    order=list(range(count+extras));rng.shuffle(order)
    # Neither position nor numeric color order determines the correspondence.
    for k in range(count):
        y=ar+1+(k//nc)*(mh+3);x=ac+1+(k%nc)*(mw+3)
        for r in range(y,y+mh+2):
            for c in range(x,x+mw+2):grid[r][c]=palette[k]
    for slot,k in enumerate(order):
        y=sy+1+(slot//cols)*(mh+1);x=sx+1+(slot%cols)*(mw+1)
        for r,c in masks[k]:grid[y+r][x+c]=palette[k]
    transform=rng.randrange(8)
    if transform&4:grid=[row[::-1] for row in grid]
    for _ in range(transform%4):grid=[list(row) for row in zip(*grid[::-1])]
    analyse(grid)
    return grid

def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard') or overrides:
        raise ValueError('unsupported difficulty or override')
    return sample(seed,sample_index)

def check_invariants(grid):
    try:analyse(grid)
    except ValueError as error:return [str(error)]
    return []
