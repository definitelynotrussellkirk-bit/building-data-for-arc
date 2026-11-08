"""Recover a rectangular 8-occluded patch from mirrored/transposed orbits."""
from __future__ import annotations
from collections import Counter,defaultdict
import hashlib
import random

MODES=('patch','marker_bbox')
RIVALS=('mirror_only','vertical_only','horizontal_only','transpose_output','rotate180_output','return_mask','fixed_inner_crop','most_frequent_bbox','first_color_bbox')


def validate_grid(grid):
    if type(grid) is not list or not 6<=len(grid)<=30 or any(type(row) is not list or len(row)!=len(grid) for row in grid):
        raise ValueError('expected a square grid from 6x6 through 30x30')
    if (len(grid)+2)%4!=0:
        raise ValueError('side must have form 4b-2')
    if any(type(v) is not int or not 0<=v<=9 for row in grid for v in row):
        raise ValueError('expected exact integer ARC colors')
    hidden=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==8]
    if not hidden:raise ValueError('missing color-8 occluder')
    r0=min(r for r,c in hidden);r1=max(r for r,c in hidden);c0=min(c for r,c in hidden);c1=max(c for r,c in hidden)
    if set(hidden)!={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}:
        raise ValueError('color 8 must be one solid rectangle')
    if len(hidden)==len(grid)*len(grid):raise ValueError('occluder cannot cover the whole grid')
    return r0,r1,c0,c1


def orbit(n,r,c,include_transpose=True):
    b=(n+2)//4;axis=n+1
    result={(r,c),(axis-r,c),(r,axis-c),(axis-r,axis-c)}
    rr=min(r,axis-r);cc=min(c,axis-c)
    off_diagonal=(rr<b<=cc<2*b) or (cc<b<=rr<2*b)
    if include_transpose and off_diagonal:
        tr,tc=cc,rr
        result|={(tr,tc),(axis-tr,tc),(tr,axis-tc),(axis-tr,axis-tc)}
    return {(x,y) for x,y in result if 0<=x<n and 0<=y<n}


def orbit_key(n,r,c):
    return min(orbit(n,r,c,True))


def visible_values(grid,r,c,include_transpose=True):
    return {grid[x][y] for x,y in orbit(len(grid),r,c,include_transpose) if grid[x][y]!=8}


def analyze(grid):
    bbox=validate_grid(grid);n=len(grid);conflicts=0
    seen=set()
    for r in range(n):
        for c in range(n):
            key=orbit_key(n,r,c)
            if key in seen:continue
            seen.add(key)
            if len(visible_values(grid,r,c))>1:conflicts+=1
    r0,r1,c0,c1=bbox
    missing=sum(not visible_values(grid,r,c) for r in range(r0,r1+1) for c in range(c0,c1+1))
    if conflicts:raise ValueError('visible cells conflict within a required symmetry orbit')
    if missing:raise ValueError('occluder hides every member of a required symmetry orbit')
    return {'bbox':bbox,'side':n,'block':(n+2)//4,'visible_orbit_conflicts':conflicts,'unrecoverable_hidden_cells':missing}


def _recover(grid,candidates):
    r0,r1,c0,c1=validate_grid(grid);n=len(grid);axis=n+1
    out=[]
    for r in range(r0,r1+1):
        row=[]
        for c in range(c0,c1+1):
            if candidates=='full':coords=orbit(n,r,c,True)
            elif candidates=='mirror':coords=orbit(n,r,c,False)
            elif candidates=='vertical':coords={(r,c),(r,axis-c)}
            elif candidates=='horizontal':coords={(r,c),(axis-r,c)}
            else:raise ValueError('unknown recovery candidate set')
            vals={grid[x][y] for x,y in coords if 0<=x<n and 0<=y<n and grid[x][y]!=8}
            row.append(next(iter(vals)) if len(vals)==1 else 8)
        out.append(row)
    return out


def recover_patch(grid):
    analyze(grid);patch=_recover(grid,'full')
    if any(v==8 for row in patch for v in row):raise ValueError('patch recovery incomplete')
    return patch


def rarest_marker(patch):
    counts=Counter(v for row in patch for v in row)
    minimum=min(counts.values());colors=[color for color,count in counts.items() if count==minimum]
    if len(colors)!=1:raise ValueError('marker_bbox requires one uniquely rare color')
    color=colors[0];cells=[(r,c) for r,row in enumerate(patch) for c,v in enumerate(row) if v==color]
    r0=min(r for r,c in cells);r1=max(r for r,c in cells);c0=min(c for r,c in cells);c1=max(c for r,c in cells)
    return color,(r0,r1,c0,c1)


def _crop_color_bbox(patch,color):
    cells=[(r,c) for r,row in enumerate(patch) for c,v in enumerate(row) if v==color]
    r0=min(r for r,c in cells);r1=max(r for r,c in cells);c0=min(c for r,c in cells);c1=max(c for r,c in cells)
    return [row[c0:c1+1] for row in patch[r0:r1+1]]


def solve(grid,mode='patch',rival=None):
    if mode not in MODES:raise ValueError('output mode must be patch or marker_bbox')
    patch=recover_patch(grid)
    if rival is None:
        if mode=='patch':return patch
        color,_=rarest_marker(patch);return _crop_color_bbox(patch,color)
    if rival=='mirror_only':return _recover(grid,'mirror')
    if rival=='vertical_only':return _recover(grid,'vertical')
    if rival=='horizontal_only':return _recover(grid,'horizontal')
    if rival=='transpose_output':return [list(row) for row in zip(*patch)]
    if rival=='rotate180_output':return [list(reversed(row)) for row in reversed(patch)]
    if rival=='return_mask':return [[8]*len(patch[0]) for _ in patch]
    if rival=='fixed_inner_crop':
        return [row[1:-1] for row in patch[1:-1]] if len(patch)>2 and len(patch[0])>2 else patch
    counts=Counter(v for row in patch for v in row)
    if rival=='most_frequent_bbox':
        color=max(sorted(counts),key=lambda x:counts[x]);return _crop_color_bbox(patch,color)
    if rival=='first_color_bbox':return _crop_color_bbox(patch,patch[0][0])
    raise ValueError('unknown rival')


def rng_for(seed,tag):
    if type(seed) is not int:raise ValueError('seed must be an exact integer')
    raw=hashlib.sha256(f'0934a4d8/v1/{seed}/{tag}'.encode()).digest()
    return random.Random(int.from_bytes(raw,'big'))


_DEMO_PROFILES=((4,5,3,'left'),(5,4,6,'right'),(6,6,4,'top'),(7,5,7,'interior'),(8,9,4,'right'),(6,4,5,'bottom'))
_QUERY_PROFILES=((5,6,3,'left'),(6,5,6,'interior'),(7,7,4,'right'),(8,9,3,'left'))


def _placements(rng,n,h,w,kind):
    if kind=='left':items=[(r,0) for r in range(n-h+1)]
    elif kind=='right':items=[(r,n-w) for r in range(n-h+1)]
    elif kind=='top':items=[(0,c) for c in range(n-w+1)]
    elif kind=='bottom':items=[(n-h,c) for c in range(n-w+1)]
    elif kind=='interior':items=[(r,c) for r in range(1,n-h) for c in range(1,n-w)]
    else:raise ValueError('unknown placement kind')
    rng.shuffle(items)
    # Prefer masks crossing the inner reflection seam; this forces transpose evidence.
    seam=n//2
    items.sort(key=lambda p:0 if p[0]<=seam<=p[0]+h-1 or p[1]<=seam<=p[1]+w-1 else 1)
    return items


def _scene(rng,b,h,w,kind):
    n=4*b-2;marker,fill1,fill2,*outside=rng.sample([c for c in range(10) if c!=8],6)
    for r0,c0 in _placements(rng,n,h,w,kind):
        mask={(r,c) for r in range(r0,r0+h) for c in range(c0,c0+w)}
        if any(not (orbit(n,r,c)-mask) for r,c in mask):continue
        groups=defaultdict(list)
        for r,c in mask:groups[orbit_key(n,r,c)].append((r,c))
        candidates=[]
        for key,cells in groups.items():
            if len(cells)==1:candidates.append((key,cells[0]))
        best=None
        for i,(ka,a) in enumerate(candidates):
            for kb,z in candidates[i+1:]:
                rr0=min(a[0],z[0]);rr1=max(a[0],z[0]);cc0=min(a[1],z[1]);cc1=max(a[1],z[1])
                bh,bw=rr1-rr0+1,cc1-cc0+1
                if bh*bw<6 or (bh==h and bw==w):continue
                score=bh*bw
                if best is None or score>best[0]:best=(score,ka,kb)
        if best is None:continue
        marker_keys={best[1],best[2]}
        nonmarker=sorted(set(groups)-marker_keys)
        patch_assignment=None
        for _ in range(128):
            candidate={key:rng.choice((fill1,fill2,outside[0])) for key in nonmarker}
            candidate.update({key:marker for key in marker_keys})
            patch=[[candidate[orbit_key(n,r0+rr,c0+cc)] for cc in range(w)] for rr in range(h)]
            counts=Counter(v for row in patch for v in row)
            if counts.get(marker)!=2 or min((count for color,count in counts.items() if color!=marker),default=0)<=2:continue
            if [color for color,count in counts.items() if count==min(counts.values())]!=[marker]:continue
            mr=[(r,c) for r,row in enumerate(patch) for c,v in enumerate(row) if v==marker]
            br0=min(r for r,c in mr);br1=max(r for r,c in mr);bc0=min(c for r,c in mr);bc1=max(c for r,c in mr)
            if br0==0 and br1==h-1 and bc0==0 and bc1==w-1:continue
            marker_crop=[row[bc0:bc1+1] for row in patch[br0:br1+1]]
            # The demonstrations must distinguish both supported settings
            # from tempting color-frequency shortcuts in either direction.
            first_crop=_crop_color_bbox(patch,patch[0][0])
            most_frequent=max(sorted(counts),key=lambda color:counts[color])
            frequent_crop=_crop_color_bbox(patch,most_frequent)
            if patch[0][0]==marker:continue
            if first_crop in (patch,marker_crop) or frequent_crop in (patch,marker_crop):continue
            patch_assignment=candidate
            break
        if patch_assignment is None:continue
        all_keys={orbit_key(n,r,c) for r in range(n) for c in range(n)}
        assignment={key:rng.choice((fill1,fill2,*outside)) for key in all_keys}
        assignment.update(patch_assignment)
        full=[[assignment[orbit_key(n,r,c)] for c in range(n)] for r in range(n)]
        grid=[row[:] for row in full]
        for r,c in mask:grid[r][c]=8
        try:
            if recover_patch(grid)!=patch:continue
            if solve(grid,'marker_bbox')==patch:continue
        except ValueError:continue
        return grid
    raise RuntimeError('bounded occlusion construction exhausted')


def sample_input(seed,index,*,query=False):
    if type(index) is not int or index<0 or type(query) is not bool:raise ValueError('invalid scene index or query flag')
    profiles=_QUERY_PROFILES if query else _DEMO_PROFILES
    b,h,w,kind=profiles[index%len(profiles)]
    return _scene(rng_for(seed,f'{"query" if query else "demo"}/{index}'),b,h,w,kind)


def query_order(seed):
    order=list(range(4));rng_for(seed,'presentation').shuffle(order);return order
