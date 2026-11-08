"""Public 3a25b0d8: isolate figures and transfer spatially matched cavity colors.

Standalone base sampler: standard library and shared GenCtx only. No filesystem
reads or adjacent workspace imports during generation. Geometry and Python label
claims live here; Racket remains the label authority via the native adapter.
"""
from __future__ import annotations
from collections import Counter
import copy
from puzzle_generators.base import gen_ctx
TASK_ID=GENERATOR_ID='public_eval_3a25b0d8'
RULE_TASK_ID='ee_3a25b0d8'
VERSION='1.0.1'
EXAMPLES_NEEDED=2
SUMMARY='Public 3a25b0d8: isolate figures and transfer spatially matched cavity colors.'
AXES={}
SCOPES=('all','expanded_only')

def _int(value,low,high,name):
    if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value

def bbox(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)

def spatial_key(cells):
    r0,c0,r1,c1=bbox(cells);return r0+r1,c0+c1

def regions(grid,predicate,connectivity=4):
    H,W=len(grid),len(grid[0]);seen=set();result=[]
    steps=[(r,c) for r in (-1,0,1) for c in (-1,0,1) if (r or c) and (connectivity==8 or abs(r)+abs(c)==1)]
    for r in range(H):
        for c in range(W):
            if (r,c) in seen or not predicate(grid[r][c]):continue
            seen.add((r,c));pending=[(r,c)];cells=[]
            while pending:
                y,x=pending.pop();cells.append((y,x))
                for dy,dx in steps:
                    yy,xx=y+dy,x+dx
                    if 0<=yy<H and 0<=xx<W and (yy,xx) not in seen and predicate(grid[yy][xx]):
                        seen.add((yy,xx));pending.append((yy,xx))
            result.append(sorted(cells))
    return result

def analyse(grid):
    if type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30:raise ValueError('grid dimensions must be 1..30')
    W=len(grid[0])
    if any(type(row) is not list or len(row)!=W or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):raise ValueError('invalid integer grid')
    bg=Counter(v for row in grid for v in row).most_common(1)[0][0]
    objects=regions(grid,lambda v:v!=bg,8)
    if len(objects)!=2:raise ValueError('exactly two disconnected figures required')
    blank=[o for o in objects if len({grid[r][c] for r,c in o})==1]
    if len(blank)!=1:raise ValueError('exactly one blank outline required')
    target=blank[0];source=next(o for o in objects if o is not target);wall=grid[target[0][0]][target[0][1]]
    def crop(cells):
        r0,c0,r1,c1=bbox(cells);occupied=set(cells)
        return [[grid[r][c] if (r,c) in occupied else bg for c in range(c0,c1+1)] for r in range(r0,r1+1)]
    def holes(canvas):
        raw=regions(canvas,lambda v:v!=wall)
        inside=[o for o in raw if all(0<r<len(canvas)-1 and 0<c<len(canvas[0])-1 for r,c in o)]
        return sorted(inside,key=spatial_key)
    s,t=crop(source),crop(target);sr,tr=holes(s),holes(t)
    if not sr or len(sr)!=len(tr):raise ValueError('guide/target cavity counts differ or empty')
    if any(len({s[r][c] for r,c in o})!=1 or s[o[0][0]][o[0][1]] in (bg,wall) for o in sr):raise ValueError('guide cavities must have one non-background color each')
    return dict(bg=bg,wall=wall,source=s,target=t,source_regions=sr,target_regions=tr,source_cells=source,target_cells=target)

def solve(grid,scope='all',foil=None):
    if scope not in SCOPES:raise ValueError('unknown transfer scope')
    f=analyse(grid);s=f['source'];out=copy.deepcopy(f['target']);sr=f['source_regions'];tr=f['target_regions']
    color=lambda cells:s[cells[0][0]][cells[0][1]]
    if foil=='both_scan':sr=sorted(sr,key=min);tr=sorted(tr,key=min)
    elif foil=='source_scan':sr=sorted(sr,key=min)
    elif foil=='target_scan':tr=sorted(tr,key=min)
    elif foil=='source_area':sr=sorted(sr,key=lambda o:(len(o),spatial_key(o)))
    elif foil=='target_area':tr=sorted(tr,key=lambda o:(len(o),spatial_key(o)))
    elif foil=='reverse':sr=sr[::-1]
    elif foil=='numeric_colors':sr=sorted(sr,key=lambda o:(color(o),spatial_key(o)))
    elif foil=='guide_copy':return copy.deepcopy(s)
    for source,target in zip(sr,tr):
        paint=scope=='all' or len(target)>len(source)
        if foil=='nonshrunk':paint=scope=='all' or len(target)>=len(source)
        if foil=='shrunk':paint=scope=='all' or len(target)<len(source)
        if foil=='always':paint=True
        value=color(sr[0]) if foil=='first_color' else color(source)
        if paint:
            for r,c in target:out[r][c]=value
    return out

def _figure(width,band_counts,heights,colors,widths,notches,corner_codes,rng,bg,wall,filled):
    height=sum(heights)+len(heights)+1
    grid=[[wall]*width for _ in range(height)];allholes=[];y=1;k=0
    for n,bh in zip(band_counts,heights):
        centers=[width//2] if n==1 else ([3,width-4] if n==2 else [2,6,10])
        for j,center in enumerate(centers):
            # A short middle region shares the same center row with tall side
            # regions. Pixel scan order is therefore NOT the correspondence.
            hh=bh-2 if n==3 and j==1 and bh>=3 else bh
            ww=widths[k];top=y+(bh-hh)//2;left=center-ww//2
            cells={(r,c) for r in range(top,top+hh) for c in range(left,left+ww)}
            if notches[k] and hh>=2:
                code=corner_codes[k];cells.remove((top+(hh-1 if code&2 else 0),left+(ww-1 if code&1 else 0)))
            for r,c in cells:grid[r][c]=colors[k] if filled else bg
            allholes.extend(cells);k+=1
        y+=bh+1
    # Vary the silhouette while protecting every cavity with one wall cell.
    for r in range(height):
        nearby=[c for y,c in allholes if abs(y-r)<=1]
        left_limit=min(2,min(nearby)-1) if nearby else 2
        right_limit=min(2,width-2-max(nearby)) if nearby else 2
        for c in range(rng.randrange(left_limit+1)):grid[r][c]=bg
        for off in range(rng.randrange(right_limit+1)):grid[r][width-1-off]=bg
    return grid

def sample(seed,index):
    _int(seed,0,2**63-1,'seed');_int(index,0,2**31-1,'sample_index')
    ctx=gen_ctx(seed=seed,sample_index=index,version='1.0',task_id=TASK_ID);rng=ctx.draw_rng('paired_deformed_regions')
    profile=index%4
    counts,sh,th,width=(
        ((2,3,2),(3,2,2),(2,3,2),13),
        ((1,3,1,2),(2,3,2,3),(4,2,3,2),13),
        ((2,1,3,1),(3,1,3,2),(2,3,2,4),13),
        ((2,3,1,2,1),(3,3,4,2,3),(4,4,2,4,3),13),
    )[profile]
    bg,wall=rng.sample(list(range(10)),2);palette=rng.sample([v for v in range(10) if v not in(bg,wall)],8)
    n=sum(counts);colors=[palette[k%8] for k in range(n)]
    widths=[(rng.choice([3,5]) if count==1 else 3) for count in counts for _ in range(count)]
    notches=[rng.choice([False,True]) for _ in range(n)]
    s=_figure(width,counts,sh,colors,widths,notches,[rng.randrange(4) for _ in range(n)],rng,bg,wall,True)
    t=_figure(width,counts,th,colors,widths,notches,[rng.randrange(4) for _ in range(n)],rng,bg,wall,False)
    H=30 if profile==3 else max(len(s),len(t))+6;W=2*width+4
    grid=[[bg]*W for _ in range(H)]
    sy=0 if profile==3 else rng.randrange(H-len(s)+1);ty=H-len(t) if profile==3 else rng.randrange(H-len(t)+1)
    sx=0 if profile==3 else 1;tx=W-width if profile==3 else W-width-1
    for piece,y,x in [(s,sy,sx),(t,ty,tx)]:
        for r,row in enumerate(piece):
            for c,v in enumerate(row):grid[y+r][x+c]=v
    if profile==3:
        # An exterior connected whisker makes figure bounding boxes overlap
        # without touching the other component. Cropping without isolating
        # components would now import the other figure's pixels.
        end=max(c for c,v in enumerate(grid[sy]) if v==wall)
        for c in range(end+1,tx+3):grid[sy][c]=wall
    transform=rng.choice([0,2,4,6]) if profile in (0,1) else rng.randrange(8)
    if transform&4:grid=[row[::-1] for row in grid]
    for _ in range(transform%4):grid=[list(row) for row in zip(*grid[::-1])]
    facts=analyse(grid)
    if facts['bg']!=bg:raise ValueError('background must remain the modal color')
    return grid

def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard') or overrides:
        raise ValueError('unsupported difficulty or override')
    return sample(seed,sample_index)

def check_invariants(grid):
    try:analyse(grid)
    except ValueError as error:return [str(error)]
    return []
