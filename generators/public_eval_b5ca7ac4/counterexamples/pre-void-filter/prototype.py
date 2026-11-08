"""Uniform-frame recovery and collision-aware horizontal packing, no fixture lookup."""
from __future__ import annotations
from collections import Counter
from typing import NamedTuple, Any
import hashlib,random
SETTINGS=('front_first','top_first')

class Box(NamedTuple):
    r:int
    c:int
    h:int
    w:int
    border:int
    fill:int
    original_c:int

def checked_grid(g: Any) -> list[list[int]]:
    if (type(g) is not list or not 1<=len(g)<=30 or any(type(row) is not list for row in g)
        or not 1<=len(g[0])<=30 or any(len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected rectangular integer-color grid, dimensions 1..30')
    return g

def background(g):
    return Counter(v for row in g for v in row).most_common(1)[0][0]

def extract(grid: list[list[int]]) -> list[Box]:
    g=checked_grid(grid);h,w=len(g),len(g[0]);found=[]
    for r in range(h-2):
        for c in range(w-2):
            b=g[r][c]
            if b not in (2,8) or g[r+1][c]!=b or g[r][c+1]!=b or g[r+1][c+1]==b:continue
            fill=g[r+1][c+1]
            # Candidate boundaries must be fully framed with a uniform different interior.
            for rr in range(r+2,h):
                if g[rr][c]!=b:continue
                for cc in range(c+2,w):
                    if g[r][cc]!=b or g[rr][cc]!=b:continue
                    if all(g[i][j]==(b if i in (r,rr) or j in (c,cc) else fill)
                           for i in range(r,rr+1) for j in range(c,cc+1)):
                        found.append(Box(r,c,rr-r+1,cc-c+1,b,fill,c))
    return found

def pack(boxes:list[Box],width:int,order:str='front_first',*,raw_obstacles:bool=False) -> list[Box]:
    if order not in SETTINGS:raise ValueError('Unknown packing_order')
    answer=[]
    for border in (8,2):
        left=border==8
        group=[b for b in boxes if b.border==border]
        group.sort(key=(lambda b:(b.c if left else -b.c,b.r)) if order=='front_first'
                       else (lambda b:(b.r,b.c if left else -b.c)))
        settled=[]
        for b in group:
            hits=[p for p in settled if b.r<p.r+p.h and p.r<b.r+b.h]
            col=lambda p:p.original_c if raw_obstacles else p.c
            destination=max((col(p)+p.w for p in hits),default=0) if left else min((col(p)-b.w for p in hits),default=width-b.w)
            settled.append(b._replace(c=destination))
        answer+=settled
    return answer

def paint(h:int,w:int,bg:int,boxes:list[Box]) -> list[list[int]]:
    out=[[bg]*w for _ in range(h)]
    for b in boxes:
        for i in range(b.h):
            for j in range(b.w):
                if 0<=b.r+i<h and 0<=b.c+j<w:
                    out[b.r+i][b.c+j]=b.border if i in (0,b.h-1) or j in (0,b.w-1) else b.fill
    return out

def solve(grid,packing_order='front_first'):
    g=checked_grid(grid)
    return paint(len(g),len(g[0]),background(g),pack(extract(g),len(g[0]),packing_order))

def validate_request(seed,demos,queries):
    for v,lo,hi,name in ((seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')):
        if type(v) is not int or not lo<=v<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')

def scene(seed:int,index:int,*,query:bool=False,rng:random.Random|None=None):
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0:raise ValueError('Invalid seed/index')
    if rng is None:rng=random.Random(int.from_bytes(hashlib.sha256(f'b5ca7ac4-v1|{seed}|{query}|{index}'.encode()).digest(),'big'))
    h,w=((22,24),(26,23),(28,27),(30,30))[index%4] if query else (22+index%6,22+index%6)
    n=4 if query and index%4==3 else (2 if index%3==2 else 3)
    bg=rng.choice((0,1,3,4,5,6,7,9));boxes=[]
    borders=[8,2]
    if rng.choice((False,True)):borders.reverse()
    for band,border in enumerate(borders):
        bh=rng.choice((4,5));step=2;span=bh+step*(n-1)
        start=0 if band==0 else h-span
        widths=[rng.randint(3,5) for _ in range(n)]
        slack=w-sum(widths)-(n-1)
        gaps=[1]*(n-1)
        for _ in range(slack):gaps[rng.randrange(n-1)]+=1
        columns=[0]
        for k in range(n-1):columns.append(columns[-1]+widths[k]+gaps[k])
        if n==4:ranks=[2,0,3,1]
        elif n==3 and index%2:ranks=[1,0,2]
        else:ranks=list(reversed(range(n)))
        if border==2:ranks=[n-1-k for k in ranks]
        for j,rank in enumerate(ranks):
            fill=rng.choice([c for c in range(10) if c not in (bg,border)])
            if j==0:fill=2 if border==8 else 8
            c=columns[rank]
            boxes.append(Box(start+j*step,c,bh,widths[rank],border,fill,c))
    return paint(h,w,bg,boxes)
