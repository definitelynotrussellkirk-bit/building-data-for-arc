"""Recover a decorated anchor, then scale and reflect its pixel geometry.

Python emits claim labels; canonical and alternative Racket execute independently.
No original task data, solution tables or neighboring homes are imported.
"""
from __future__ import annotations
import hashlib
import random
from functools import lru_cache

MODES=('panel_reflections','preserve_orientation')
BG,DIVIDER,ANCHOR=4,1,2


def integer(value,low:int,high:int,name:str)->int:
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an integer in {low}..{high}')
    return value


def analyse(grid:list[list[int]])->dict:
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or
        not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0]) or
            any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected a rectangular exact integer color grid of size 1..30')
    H,W=len(grid),len(grid[0])
    rows=[r for r in range(H) if all(v==DIVIDER for v in grid[r])]
    cols=[c for c in range(W) if all(grid[r][c]==DIVIDER for r in range(H))]
    if len(rows)!=1 or len(cols)!=1 or not 1<=rows[0]<H-1 or not 1<=cols[0]<W-1:
        raise ValueError('expected one interior full blue row and column')
    dr,dc=rows[0],cols[0];panels=[]
    for pr,(r0,r1) in enumerate(((0,dr-1),(dr+1,H-1))):
        for pc,(c0,c1) in enumerate(((0,dc-1),(dc+1,W-1))):
            reds=[(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1) if grid[r][c]==ANCHOR]
            if not reds:raise ValueError('each panel needs a red anchor')
            ar,ac=min(r for r,c in reds),min(c for r,c in reds)
            br,bc=max(r for r,c in reds),max(c for r,c in reds)
            size=br-ar+1
            if bc-ac+1!=size or len(reds)!=size*size:
                raise ValueError('red anchors must be solid squares')
            decoration=[(r,c,grid[r][c]) for r in range(r0,r1+1) for c in range(c0,c1+1) if grid[r][c] not in (BG,ANCHOR)]
            panels.append({'panel':[pr,pc],'bounds':[r0,c0,r1,c1],
                           'anchor':[ar,ac,br,bc],'size':size,'decoration':decoration})
    sources=[p for p in panels if p['decoration']]
    if len(sources)!=1:raise ValueError('expected exactly one decorated source panel')
    return {'divider':[dr,dc],'panels':panels,'source':sources[0]}


def render(grid:list[list[int]],data:dict,mode:str,foil:str|None=None)->list[list[int]]:
    out=[row[:] for row in grid]
    source=data['panels'][0] if foil=='source_topleft' else data['source']
    sr,sc,_,_=source['anchor'];native=source['size']
    r0,c0,r1,c1=source['bounds']
    for target in data['panels']:
        if target is source:continue
        tr,tc,_,_=target['anchor'];k=target['size']
        if foil=='same_scale_only' and k!=native:continue
        if foil=='integer_scale_only' and k%native:continue
        fy=mode=='panel_reflections' and target['panel'][0]!=source['panel'][0]
        fx=mode=='panel_reflections' and target['panel'][1]!=source['panel'][1]
        if foil=='swap_flip_axes':fy,fx=fx,fy
        elif foil=='always_flip_both':fy=fx=True
        elif foil=='always_flip_x':fy,fx=False,True
        elif foil=='always_flip_y':fy,fx=True,False
        ratio_numerator=k if foil=='no_scaling' else (2 if foil=='fixed_native_two' else native)
        top,left,bottom,right=target['bounds']
        for r in range(top,bottom+1):
            for c in range(left,right+1):
                if grid[r][c]!=BG:continue
                rr=k-1-(r-tr) if fy else r-tr
                cc=k-1-(c-tc) if fx else c-tc
                # Floor, not truncation, is essential for negative anchor offsets.
                ur=rr*ratio_numerator//k;uc=cc*ratio_numerator//k
                if foil=='truncate_inverse':
                    ur=(abs(rr*ratio_numerator)//k)*(1 if rr>=0 else -1)
                    uc=(abs(cc*ratio_numerator)//k)*(1 if cc>=0 else -1)
                if foil=='macrocell_only':ur=(ur//native)*native;uc=(uc//native)*native
                y,x=sr+ur,sc+uc
                if r0<=y<=r1 and c0<=x<=c1:
                    v=grid[y][x]
                    if v in (BG,ANCHOR) or (foil=='omit_blue' and v==1) or (foil=='omit_black' and v==0):continue
                    out[r][c]=v
    return out


def solve(grid:list[list[int]],mode:str='panel_reflections')->list[list[int]]:
    if mode not in MODES:raise ValueError('unknown orientation mode')
    return render(grid,analyse(grid),mode)


@lru_cache(maxsize=2048)
def _policies(key:tuple)->dict:
    grid=[list(r) for r in key];data=analyse(grid)
    out={mode:render(grid,data,mode) for mode in MODES}
    for mode in MODES:
        for foil in ('source_topleft','same_scale_only','integer_scale_only','swap_flip_axes',
                     'always_flip_both','always_flip_x','always_flip_y','no_scaling',
                     'truncate_inverse','macrocell_only','omit_blue','omit_black','fixed_native_two'):
            out[mode+':'+foil]=render(grid,data,mode,foil)
    out['unchanged']=[row[:] for row in grid]
    return out


def policy_outputs(grid:list[list[int]])->dict:
    return _policies(tuple(tuple(row) for row in grid))


def sample(seed:int,index:int,*,stress:bool=False)->list[list[int]]:
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'panel-v1:{seed}:{index}'.encode()).digest(),'big'))
    native=3 if stress else (2,3,1,2,2,1)[index%6]
    fine=index%2==0 and native==2 and not stress
    H=30 if stress else rng.choice((25,27,29))
    W=30 if stress else rng.choice((25,27,29))
    dr=H//2;dc=W//2
    grid=[[BG]*W for _ in range(H)];grid[dr]=[DIVIDER]*W
    for row in grid:row[dc]=DIVIDER
    bounds=[(0,0,dr-1,dc-1),(0,dc+1,dr-1,W-1),
            (dr+1,0,H-1,dc-1),(dr+1,dc+1,H-1,W-1)]
    source_offset=int.from_bytes(hashlib.sha256(f'panel-source:{seed}'.encode()).digest(),'big')%4
    source_index=(source_offset+index)%4
    sizes=[3,4,5] if stress else ([2,4,2] if fine else [1,3,2])
    rng.shuffle(sizes);sizes.insert(source_index,native)
    anchors=[]
    for i,((r0,c0,r1,c1),k) in enumerate(zip(bounds,sizes)):
        r=r0+(r1-r0+1-k)//2 + (0 if i==source_index else rng.randrange(-1,2))
        c=c0+(c1-c0+1-k)//2 + (0 if i==source_index else rng.randrange(-1,2))
        if stress and i!=source_index:
            # Destination clipping on an outer or divider boundary is exercised.
            r=r0+1 if i<2 else r1-k
            c=c0+1 if i%2==0 else c1-k
        anchors.append((r,c))
        for rr in range(k):
            for cc in range(k):grid[r+rr][c+cc]=ANCHOR
    sr,sc=anchors[source_index]
    palette=[0,1]+rng.sample([3,5,6,7,8,9],4)
    rng.shuffle(palette)
    if fine:
        # One-pixel features inside a two-pixel anchor unit cannot be replaced by
        # uniformly colored macrocells. Integer 1x/2x scales retain every feature.
        cells=[(r,c) for r in range(-2,4) for c in range(-2,4) if not(0<=r<2 and 0<=c<2)]
        rng.shuffle(cells)
        for i,(r,c) in enumerate(cells[:rng.randrange(10,19)]):
            grid[sr+r][sc+c]=palette[i%len(palette)]
    else:
        blocks=[(-1,0),(0,-1),(0,1),(1,0)]
        corners=[(-1,-1),(-1,1),(1,-1),(1,1)];rng.shuffle(corners)
        blocks+=corners[:2 if stress else rng.randint(1,3)]
        rng.shuffle(blocks)
        for i,(br,bc) in enumerate(blocks):
            for r in range(native):
                for c in range(native):grid[sr+br*native+r][sc+bc*native+c]=palette[i%len(palette)]
    analyse(grid)
    return grid
