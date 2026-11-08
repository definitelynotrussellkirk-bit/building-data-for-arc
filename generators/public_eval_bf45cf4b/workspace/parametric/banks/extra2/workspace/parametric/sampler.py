"""Construct independent layout/motif roles with visible, variable boundary ports."""
import random


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def transpose(g):return [list(r) for r in zip(*g)]


def motif(rng,h,w,axis,palette,bg):
    hh,ww=(w,h) if axis=='vertical' else (h,w);middle=hh//2
    cells=set()
    for c in range(ww):
        up=middle if c==0 else rng.randrange(middle)
        down=hh-1-middle if c==ww-1 else rng.randrange(max(1,hh-1-middle))
        for r in range(middle-up,middle+down+1):cells.add((r,c))
    if axis=='both':cells.update((r,ww//2) for r in range(hh))
    out=[[bg]*ww for _ in range(hh)]
    for r,c in sorted(cells):out[r][c]=rng.choice(palette)
    # One motif color spans the whole bbox, making color-role grouping unambiguous.
    out[0][0]=out[-1][-1]=palette[0]
    out[middle][0]=palette[0];out[middle][-1]=palette[1]
    if len(palette)>2:out[middle][ww//2]=palette[2]
    return transpose(out) if axis=='vertical' else out


def construct(seed,index,*,split='production',grid_h=None,grid_w=None,mask_h=None,mask_w=None,motif_h=None,motif_w=None,axis=None,motif_colors=None):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'sample_index')
    if split not in ('train','test','production'):raise ValueError('Invalid split')
    rng=random.Random(f'motif-family-v1:{split}:{seed}:{index}');stress=split=='test' and index==3;teaching=split=='train' and index<2
    H=(30 if stress else rng.randint(14,24)) if grid_h is None else integer(grid_h,14,30,'grid_h')
    W=(30 if stress else rng.randint(14,24)) if grid_w is None else integer(grid_w,14,30,'grid_w')
    default_mask=(5,5) if teaching else ((6,5) if stress else rng.choice(((3,3),(3,4),(4,3),(5,5),(6,6))))
    mh=default_mask[0] if mask_h is None else integer(mask_h,3,6,'mask_h')
    mw=default_mask[1] if mask_w is None else integer(mask_w,3,6,'mask_w')
    ph=(5 if stress else rng.randint(3,min(6,30//mh))) if motif_h is None else integer(motif_h,3,6,'motif_h')
    pw=(6 if stress else rng.randint(3,min(6,30//mw))) if motif_w is None else integer(motif_w,3,6,'motif_w')
    if mh*ph>30 or mw*pw>30:raise ValueError('Layout x motif exceeds 30x30')
    axis=(('horizontal' if index==0 else 'vertical') if teaching else rng.choice(('horizontal','vertical','both'))) if axis is None else axis
    if type(axis) is not str or axis not in ('horizontal','vertical','both'):raise ValueError('Unknown motif connection axis')
    number=rng.choice((2,3)) if motif_colors is None else integer(motif_colors,2,3,'motif_colors')
    bg=rng.choice(range(1,9)) if teaching and index==0 else rng.randrange(9)
    palette=[v for v in range(9) if v!=bg];rng.shuffle(palette);key=palette[0];motif_palette=palette[1:number+1]
    tile=motif(rng,ph,pw,axis,motif_palette,bg)
    if teaching and min(mh,mw)>=5:
        hh,ww=(mw,mh) if axis=='vertical' else (mh,mw)
        layout=[[bg]*ww for _ in range(hh)];layout[0]=[key]*ww
        left=rng.randrange(ww-1)
        for r in range(2,hh):layout[r][left]=layout[r][left+1]=key
        if index==0:layout=layout[::-1]  # longest expanded run last in demo zero
        if axis=='vertical':layout=transpose(layout)
    else:
        layout=[[key if rng.random()<rng.uniform(.30,.70) else bg for _ in range(mw)] for _ in range(mh)]
        # Tight bbox and meaningful holes; no assumption of component connectedness.
        layout[0][rng.randrange(mw)]=key;layout[-1][rng.randrange(mw)]=key
        layout[rng.randrange(mh)][0]=key;layout[rng.randrange(mh)][-1]=key
        layout[mh//2][mw//2]=bg
    g=[[bg]*W for _ in range(H)]
    horizontal=rng.choice((False,True));layout_first=rng.choice((False,True))
    if horizontal:
        gap=rng.randint(1,W-mw-pw);start=rng.randrange(W-mw-pw-gap+1)
        lc,tc=(start,start+mw+gap) if layout_first else (start+pw+gap,start)
        lr=rng.randrange(H-mh+1);tr=rng.randrange(H-ph+1)
    else:
        gap=rng.randint(1,H-mh-ph);start=rng.randrange(H-mh-ph-gap+1)
        lr,tr=(start,start+mh+gap) if layout_first else (start+ph+gap,start)
        lc=rng.randrange(W-mw+1);tc=rng.randrange(W-pw+1)
    for src,rr,cc in ((layout,lr,lc),(tile,tr,tc)):
        for r,row in enumerate(src):
            for c,v in enumerate(row):g[rr+r][cc+c]=v
    target=[]
    for row in layout:
        for rr in range(ph):
            line=[]
            for value in row:line.extend(tile[rr] if value==key else [bg]*pw)
            target.append(line)
    return g,target


def draw(seed,index,**kwargs):return construct(seed,index,**kwargs)[0]
