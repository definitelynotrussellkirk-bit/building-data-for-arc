"""Independent Python claims for continuous diagonal-span bracketing.

A segment has u=r+c, continuous v interval [r-c at first,last], and measured
length. A background cell is fillable iff a legal pair brackets its u while
both spans contain v. Racket is the source of verified labels.
"""
from __future__ import annotations
import random
BG,FILL=8,2
COLORS=(0,1,3,4,5,6,7,9)
RIVALS=('identity','opposite_mode','adjacent_only','first_pair','longest_only',
        'endpoint_rays','union_spans','redraw_strokes','color_grouping',
        'short_strokes_only','point_spans','first_four','length_thirteen')

def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in [{low}, {high}]')
    return value

def grid_copy(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or
        not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0]) or
        any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected a rectangular integer-color grid within 30x30')
    return [row[:] for row in grid]

def analyze(grid):
    grid_copy(grid);H,W=len(grid),len(grid[0]);segments=[]
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if color==BG or (r>0 and c+1<W and grid[r-1][c+1]==color):continue
            rr,cc=r,c
            while rr+1<H and cc>0 and grid[rr+1][cc-1]==color:rr+=1;cc-=1
            segments.append({'u':r+c,'lo':r-c,'hi':rr-cc,'length':rr-r+1,'color':color})
    return sorted(segments,key=lambda s:(s['u'],s['lo']))

def solve(grid,mode='all_spans',rival=None):
    out=grid_copy(grid);H,W=len(out),len(out[0])
    if mode not in ('all_spans','equal_length'):raise ValueError('Unknown bracket rule')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    if rival=='identity':return out
    if rival=='opposite_mode':mode='equal_length' if mode=='all_spans' else 'all_spans'
    segments=analyze(grid)
    if rival=='first_pair':segments=segments[:2]
    if rival=='first_four':segments=segments[:4]
    if rival=='length_thirteen':segments=[s for s in segments if s['length']<=13]
    if rival=='longest_only':
        maximum=max([s['length'] for s in segments],default=0)
        segments=[s for s in segments if s['length']==maximum]
    if rival=='short_strokes_only':segments=[s for s in segments if s['length']<=5]
    if rival=='point_spans':segments=[dict(s,hi=s['lo']) for s in segments]
    for i,left in enumerate(segments):
        for j in range(i+1,len(segments)):
            right=segments[j]
            if rival=='adjacent_only' and j!=i+1:continue
            if left['u']>=right['u']:continue
            if mode=='equal_length' and left['length']!=right['length']:continue
            if rival=='color_grouping' and left['color']!=right['color']:continue
            low=min(left['lo'],right['lo']) if rival=='union_spans' else max(left['lo'],right['lo'])
            high=max(left['hi'],right['hi']) if rival=='union_spans' else min(left['hi'],right['hi'])
            for r in range(H):
                first=max(0,left['u']+1-r,r-high)
                last=min(W-1,right['u']-1-r,r-low)
                for c in range(first,last+1):
                    if rival=='endpoint_rays' and ((r-c-left['lo'])%2 or (r-c-right['lo'])%2):continue
                    if rival=='redraw_strokes' or grid[r][c]==BG:out[r][c]=FILL
    return out

def _render(rng,H,W,specs,multicolor=True):
    colors=list(COLORS);rng.shuffle(colors);cells=[]
    for i,(u,lo,length) in enumerate(specs):
        if (u-lo)%2:raise ValueError('Nonintegral segment coordinates')
        for k in range(length):
            v=lo+2*k;r=(u+v)//2;c=(u-v)//2
            cells.append((r,c,colors[i%len(colors)] if multicolor else colors[0]))
    minr=min(r for r,c,v in cells);maxr=max(r for r,c,v in cells)
    minc=min(c for r,c,v in cells);maxc=max(c for r,c,v in cells)
    if maxr-minr>=H or maxc-minc>=W:raise ValueError('Scene exceeds canvas')
    dr=rng.randint(-minr,H-1-maxr);dc=rng.randint(-minc,W-1-maxc)
    g=[[BG]*W for _ in range(H)]
    for r,c,color in cells:
        r+=dr;c+=dc
        if g[r][c]!=BG:raise ValueError('Overlapping source strokes')
        g[r][c]=color
    if rng.randrange(2):g=[row[::-1] for row in g[::-1]]
    if rng.randrange(2):g=[list(row) for row in zip(*g)]
    return g

def _small(rng):
    a=rng.choice((3,4));b=rng.choice((4,5));offset=rng.choice((0,2))
    return [(6+offset,0,a),(11+offset,-7,b),(16+offset,2,a),(21+offset,-5,b)]

def _large(rng):
    length=rng.choice((9,10))
    return [(10,-8,length),(16,-12,13),(23,-5,length),(30,-10,11)]

def sample_input(seed,index,kind='demo',difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'sample_index')
    if kind not in ('demo','query','base'):raise ValueError('Unknown input stream')
    if difficulty not in ('easy','medium','hard'):raise ValueError('Unknown difficulty')
    rng=random.Random(f'7666fa5d:{seed}:{kind}:{index}')
    if kind=='demo':
        if index==0:return _render(rng,18,22,_small(rng),True)
        if index==1:
            return _render(rng,29,29,[(6,-6,7),(12,-10,11),(18,-14,15),(24,-20,21),
                                      (30,-18,19),(34,-14,15),(42,-10,11),(50,-6,7)],False)
        return _render(rng,22+index,26+index%3,_small(rng) if index%2==0 else _large(rng),bool(index%2))
    profile=index if kind=='query' else {'easy':0,'medium':1,'hard':3}[difficulty]
    if profile==0:return _render(rng,20,24,_small(rng),bool(seed%2))
    if profile==1:
        return _render(rng,24,24,[(8,-2,4),(13,-5,6),(18,0,4),(23,-7,8),(28,-4,6),(33,-5,8)],True)
    if profile==2:
        return _render(rng,27,25,[(10,-10,4),(16,-12,7),(22,-10,7),(16,8,4),(24,8,6),(32,8,7)],False)
    if profile==3:
        return _render(rng,30,30,[(6,-6,7),(14,-12,13),(20,-16,17),(26,-20,21),
                                  (32,-18,19),(36,-14,15),(44,-12,13),(52,-6,7)],True)
    raise ValueError('Query source index must be 0..3')
