"""General marker interpreter and matched, count-independent authoring sampler.

Only geometric 4x4 symbols are constants. No official input/output is stored here.
"""
from __future__ import annotations
import hashlib
import random
from typing import Any

CODES=(2,3,5,8)
SETTINGS=('decode','highlight_largest')

def symbol(code: int, r: int, c: int) -> int:
    if code==2: return 4 if r in (0,3) or c in (0,3) else 0
    if code==3: return 1 if ((r in (0,3) and c in (1,2)) or (c in (0,3) and r in (1,2))) else 0
    if code==5: return 6 if (r<2)==(c<2) else 0
    if code==8: return 7 if r==c or r+c==3 else 0
    return 0

def checked_grid(grid: Any) -> list[list[int]]:
    if (type(grid) is not list or not 1<=len(grid)<=30 or
        any(type(row) is not list for row in grid) or not 1<=len(grid[0])<=30 or
        any(len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected rectangular integer-color grid, dimensions 1..30')
    return grid

def components(g: list[list[int]]) -> list[list[tuple[int,int]]]:
    unseen={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v}
    result=[]
    while unseen:
        seed=min(unseen);unseen.remove(seed);stack=[seed];cells=[]
        while stack:
            r,c=stack.pop();cells.append((r,c))
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    q=(r+dr,c+dc)
                    if q in unseen: unseen.remove(q);stack.append(q)
        result.append(sorted(cells))
    return result

def targets(g: list[list[int]]) -> list[tuple[int,int,int]]:
    result=[]
    for r,row in enumerate(g):
        for c,code in enumerate(row):
            if code not in CODES: continue
            legend=r>=4 and c>=4 and all(
                not symbol(code,i,j) or g[r-4+i][c-4+j]==symbol(code,i,j)
                for i in range(4) for j in range(4))
            if not legend: result.append((r,c,code))
    return result

def solve(grid: list[list[int]], finish_rule: str='decode') -> list[list[int]]:
    g=checked_grid(grid)
    if finish_rule not in SETTINGS: raise ValueError('Unknown finish_rule')
    h,w=len(g),len(g[0]);out=[[0]*w for _ in range(h)]
    for r,c,code in targets(g):
        for dr in range(4):
            for dc in range(4):
                v=symbol(code,dr,dc)
                if v and r+dr<h and c+dc<w: out[r+dr][c+dc]=v
    if finish_rule=='highlight_largest':
        groups=components(out)
        if groups:
            selected=max(groups,key=len)
            for r,c in selected:out[r][c]=9
    return out

def validate_request(seed: int, demos: int, queries: int) -> None:
    for value,lo,hi,name in ((seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')):
        if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')

def scene(seed: int, index: int, *, query: bool=False, rng: random.Random | None=None) -> list[list[int]]:
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0:raise ValueError('Invalid seed/index')
    tag=f'dfadab01-v1|{seed}|{query}|{index}'
    if rng is None: rng=random.Random(int.from_bytes(hashlib.sha256(tag.encode()).digest(),'big'))
    if query:
        h,w=((22,23),(24,27),(28,26),(30,30))[index%4]
    else: h=w=22+index%6
    g=[[0]*w for _ in range(h)]
    # These opposing lessons distinguish painted-cell mass from raw marker count.
    small=list((3,5,8));rng.shuffle(small)
    if index%2==0:
        rows=[([2]*3,0,0),(small+[rng.choice(small)],6,w-16)]
    else:
        rows=[([2]*3,0,0),(small+[rng.choice(small),rng.choice(small)],6,w-20)]
    for codes,r,c in rows:
        for k,code in enumerate(codes): g[r][c+4*k]=code
    r=h-10
    code=rng.choice(CODES)
    for dr in range(4):
        for dc in range(4):g[r+dr][dc]=symbol(code,dr,dc)
    g[r+4][4]=code
    # An anchor may occupy a legend's zero corner (as in an official example).
    if code in (3,8) and index%3==2 and symbol(code,0,0)==0:g[r][0]=code
    g[r][8]=5;g[r][12]=8
    for k,code in enumerate(rng.sample(CODES,2)):
        g[h-4][w-8+4*k]=code
    # Lawful clipped edge anchors: expose the precise clipping convention.
    g[h-1][0]=2
    g[h-8][w-1]=3
    if rng.choice((False,True)):g=[list(row) for row in zip(*g)]
    return g
