"""Construct chains from fresh contour signatures, then scatter their pieces.

No stored puzzle grids, source-position role slots, or sampling retries. A finite
profile bank provides unique seam signatures; all input-only controls are exact.
"""
import itertools
import random


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def transform(g,code):
    out=[r[:] for r in g]
    if code>=4:out=[r[::-1] for r in out]
    for _ in range(code%4):out=[list(r) for r in zip(*out[::-1])]
    return out


def construct(seed,index,*,split='production',grid_h=None,grid_w=None,orientation_id=None,chain_count=None,chain_depth=None,piece_width=None):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'sample_index')
    if split not in ('train','test','production'):raise ValueError('Invalid split')
    rng=random.Random(f'contour-family-v1:{split}:{seed}:{index}')
    orient=rng.randrange(8) if orientation_id is None else integer(orientation_id,0,7,'orientation_id')
    # A genuinely different profile, not merely a large padded small scene.
    stress=split=='test' and index==3
    H=(30 if stress else rng.randint(24,30)) if grid_h is None else integer(grid_h,24,30,'grid_h')
    W=(30 if stress else rng.randint(24,30)) if grid_w is None else integer(grid_w,24,30,'grid_w')
    h,w=(W,H) if orient%2 else (H,W)
    width=rng.choice((5,6)) if piece_width is None else integer(piece_width,5,6,'piece_width')
    count=(1 if split=='test' and index==0 else 2) if chain_count is None else integer(chain_count,1,2,'chain_count')
    depth=(4 if stress else 3) if chain_depth is None else integer(chain_depth,2,4,'chain_depth')
    if depth==4 and h<28:raise ValueError('Depth four requires >=28 along the wall-normal dimension')
    short=(3 if stress else max(1,depth-1))
    lengths=[short,depth] if count==2 else [depth]
    profiles=[(0,*p,0) for p in itertools.product((1,2),repeat=width-2)]
    terminal=(0,*([2]*(width-2)),0);pool=[p for p in profiles if p!=terminal];rng.shuffle(pool)
    required=sum(lengths)
    if required>len(profiles):raise ValueError('Too many distinct seams for width')
    seams=pool[:required-1]+[terminal]
    wall_color=rng.choice(range(1,9));palette=[c for c in range(1,9) if c!=wall_color];rng.shuffle(palette)
    # Longest-chain terminal never gets the largest color.
    biggest=max(palette[:required])
    if palette[required-1]==biggest:palette[0],palette[required-1]=palette[required-1],palette[0]
    top=h//2-2;bottom=top+4;upper=[top]*w;lower=[bottom]*w
    specifications=[];k=0
    for chain,n in enumerate(lengths):
        side=-1 if count==2 and chain==0 else 1
        col=rng.randint(1,w-width-1);seq=seams[k:k+n]
        if side==1:
            for j,v in enumerate(seq[0]):lower[col+j]=bottom-2+v
        else:
            for j,v in enumerate(seq[0]):upper[col+j]=top+2-v
        for level in range(n):
            prevbase=-2+3*level;nextbase=prevbase+3
            first=seq[level];last=seq[level+1] if level+1<n else (0,)*width
            cells=[]
            for j in range(width):
                for r in range(prevbase+first[j]+1,nextbase+last[j]+1):
                    rr=(bottom+r) if side==1 else (top-r)
                    if not 0<=rr<h:raise ValueError('Requested chain exceeds canvas')
                    cells.append((rr,col+j))
            r0=min(r for r,c in cells);c0=min(c for r,c in cells)
            specifications.append({'local':[(r-r0,c-c0) for r,c in cells],'dest':cells,'color':palette[k+level],'depth':level+1})
        k+=n
    wall={(r,c) for c in range(w) for r in range(upper[c],lower[c]+1)}
    # Narrow nonmatching sockets occupy other tangent positions without splitting the wall.
    for c in (0,w-1):wall.discard((top,c))
    g=[[0]*w for _ in range(h)];target=[[0]*w for _ in range(h)]
    for r,c in wall:g[r][c]=target[r][c]=wall_color
    maxheight=max(1+max(r for r,c in s['local']) for s in specifications)
    capacity=(w+1)//(width+1)
    n=len(specifications)
    if n>2*capacity:raise ValueError('Canvas is too narrow for separated source pieces at this width/depth')
    above=rng.randint(max(1,n-capacity),min(capacity,n-1));below=n-above
    slots=[]
    for number,low,high in ((above,0,top-maxheight-1),(below,bottom+2,h-maxheight)):
        if low>high:raise ValueError('No separated source placement strip')
        slack=w-(number*width+number-1)
        gaps=[0]*(number+1)
        for _ in range(slack):gaps[rng.randrange(len(gaps))]+=1
        col=gaps[0]
        for j in range(number):
            slots.append((rng.randint(low,high),col));col+=width+1+gaps[j+1]
    slots.sort();deep=n-1;others=[i for i in range(n) if i!=deep];rng.shuffle(others)
    def point(r,c):
        hh,ww=h,w
        if orient>=4:c=ww-1-c
        for _ in range(orient%4):r,c=c,hh-1-r;hh,ww=ww,hh
        return r,c
    choices=list(range(n));rng.shuffle(choices);order=None;vertical_offsets=None
    # Only the teaching prefix must refute position selectors; queries remain unconstrained.
    require_neutral=split=='train' and index<2 and n>=5
    heights={i:1+max(r for r,c in specifications[i]['local']) for i in range(n)}
    for perm in itertools.permutations(others):
        for slot_index in choices:
            proposed=list(perm);proposed.insert(slot_index,deep)
            for deep_offset in range(maxheight-heights[deep]+1):
                offsets={i:0 for i in range(n)};offsets[deep]=deep_offset
                def placed_points(slot,i):
                    sr,sc=slot
                    return [point(sr+r+offsets[i],sc+c) for r,c in specifications[i]['local']]
                reading=sorted((min(placed_points(slot,i)),i) for slot,i in zip(slots,proposed))
                aligned=sorted((min((c,r) if orient%2 else (r,c) for r,c in placed_points(slot,i)),i)
                               for slot,i in zip(slots,proposed))
                neutral=deep not in (reading[0][1],reading[-1][1],aligned[0][1],aligned[-1][1])
                if not require_neutral or neutral:order=proposed;vertical_offsets=offsets;break
            if order is not None:break
        if order is not None:break
    if order is None:raise ValueError('No source-order-neutral teaching placement')
    for slot,i in zip(slots,order):
        s=specifications[i]
        for r,c in s['local']:g[slot[0]+r+vertical_offsets[i]][slot[1]+c]=s['color']
        for r,c in s['dest']:target[r][c]=s['color']
    return transform(g,orient),transform(target,orient)


def draw(seed,index,**kwargs):
    return construct(seed,index,**kwargs)[0]
