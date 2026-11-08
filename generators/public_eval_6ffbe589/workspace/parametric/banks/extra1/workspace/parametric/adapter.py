"""Native matched-input family: recover layered square, read tally bars, rotate."""
from __future__ import annotations
from collections import deque
from pathlib import Path
import copy
import hashlib
import random

BASE = Path(__file__).resolve().parent
DIRECTIONS = ('clockwise', 'counterclockwise')

def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row)!=len(grid[0])
            or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected a rectangular 1..30 integer color grid')

def bbox(cells):
    if not cells: raise ValueError('Empty geometry')
    rr,cc=zip(*cells)
    return [min(rr),min(cc),max(rr),max(cc)]

def components(grid):
    unseen={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    result=[]
    while unseen:
        start=min(unseen); unseen.remove(start); queue=[start]
        for r,c in queue:
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    q=(r+dr,c+dc)
                    if q in unseen: unseen.remove(q); queue.append(q)
        result.append(queue)
    return result

def measure(grid):
    """Return the unique recoverable layered square and outside per-color counts."""
    validate_grid(grid)
    comps=components(grid)
    if not comps: raise ValueError('No layered picture')
    core=max(comps,key=len); b=bbox(core)
    cr,cc=b[0]+b[2],b[1]+b[3]
    if cr%2 != cc%2: raise ValueError('Main component has no square center')
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    candidates=[]
    for n in range(max(b[2]-b[0]+1,b[3]-b[1]+1),min(len(grid),len(grid[0]))+1):
        if (cr-n+1)%2: continue
        r,c=(cr-n+1)//2,(cc-n+1)//2; R,C=r+n-1,c+n-1
        if r<0 or c<0 or R>=len(grid) or C>=len(grid[0]): continue
        inside=[p for p in cells if r<=p[0]<=R and c<=p[1]<=C]
        if bbox(inside)!=[r,c,R,C]: continue
        colors=sorted({grid[y][x] for y,x in inside})
        if len(colors)<2: continue
        bands=[]
        for v in colors:
            radii=[max(abs(2*y-cr),abs(2*x-cc)) for y,x in inside if grid[y][x]==v]
            bands.append((min(radii),max(radii)))
        if any(not (hi<lo2 or hi2<lo) for i,(lo,hi) in enumerate(bands) for lo2,hi2 in bands[i+1:]): continue
        inside_set=set(inside)
        outside=[p for p in cells if p not in inside_set]
        if any(grid[y][x] not in colors for y,x in outside): continue
        counts={}; valid=True
        for v in colors:
            marker=[p for p in outside if grid[p[0]][p[1]]==v]
            if marker:
                a,d,A,D=bbox(marker)
                if not ((a==A or d==D) and len(marker)==(A-a+1)*(D-d+1)):
                    valid=False; break
            counts[v]=len(marker)
        if valid: candidates.append({'box':[r,c,R,C],'counts':counts})
    if not candidates: raise ValueError('No concentric square with straight color tallies')
    # Tight concentric candidates cannot absorb the spatially separated tally bars.
    return candidates[-1]

def render(grid, state, direction='clockwise'):
    if direction not in DIRECTIONS: raise ValueError('Unknown direction')
    r,c,R,C=state['box']; n=R-r+1
    out=[[0]*n for _ in range(n)]
    sign=1 if direction=='clockwise' else -1
    for y in range(n):
        for x in range(n):
            v=grid[r+y][c+x]
            if not v: continue
            a,b=y,x
            for _ in range((sign*state['counts'][v])%4): a,b=b,n-1-a
            out[a][b]=v
    return out

def solve(grid, direction='clockwise'):
    return render(grid,measure(grid),direction)

def _setting(settings):
    if type(settings) is not dict or set(settings)!={'direction'} or type(settings['direction']) is not str or settings['direction'] not in DIRECTIONS:
        raise ValueError('settings must contain exactly direction=clockwise/counterclockwise')
    return settings['direction']

def program(settings):
    direction=_setting(settings)
    code=(BASE/'canonical.rkt').read_text()
    return code if direction=='clockwise' else code.replace('(define turn-sign 1)','(define turn-sign -1)')

def _rng(seed, namespace):
    return random.Random(int.from_bytes(hashlib.sha256(f'6ffbe589:{seed}:{namespace}'.encode()).digest(),'big'))

def _rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]

def sample(seed, index, split='train'):
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0 or split not in ('train','test'):
        raise ValueError('Invalid sample seed/index/split')
    rng=_rng(seed,f'{split}:{index}')
    ns=[16,22,14,20,12,18] if split=='train' else [14,16,20,22]
    n=ns[index%len(ns)]; count_colors=min(5,n//4)
    palette=rng.sample(range(1,10),count_colors)
    if split=='train' and index==0: counts=[0,1,2,6]
    elif split=='train' and index==1: counts=[3,4,5,7,6]
    else: counts=[rng.randrange(8) for _ in palette]
    # Structural positions are independently shuffled; no color-rank cue.
    rng.shuffle(counts); counts=counts[:count_colors]
    if split=='train' and index==1:
        maximum=palette.index(max(palette))
        if counts[maximum]%4==0:
            other=next(i for i,v in enumerate(counts) if v%4)
            counts[maximum],counts[other]=counts[other],counts[maximum]
    w=max(20,n+8 if n==22 else n); h=n+8
    picture=[[0]*n for _ in range(n)]
    for layer,color in enumerate(palette):
        cells=[(r,c) for r in range(n) for c in range(n)
               if min(min(r,c,n-1-r,n-1-c)//2,count_colors-1)==layer]
        for attempt in range(64):
            mask=[[0]*n for _ in range(n)]
            for r,c in cells:
                edge=min(r,c,n-1-r,n-1-c)
                if edge==2*layer+1 or rng.random()<0.63:mask[r][c]=color
            # Keep all outer sides and largest-component center geometrically exact.
            if layer==0:
                for r,c in [(0,0),(0,n-1),(n-1,0),(n-1,n-1)]:mask[r][c]=color
            views=[]; g=mask
            for _ in range(4):views.append(g);g=_rotate(g)
            if len({str(g) for g in views})==4:break
        else:raise ValueError('Could not sample an asymmetric layer')
        for r,c in cells:
            if mask[r][c]:picture[r][c]=color
    grid=[[0]*w for _ in range(h)]
    for r in range(n):grid[r][:n]=picture[r]
    slots=list(range(count_colors));rng.shuffle(slots)
    for color,count,slot in zip(palette,counts,slots):
        r=n+1+2*(slot//2); c=(w//2)*(slot%2)+rng.randrange(2)
        for k in range(count):grid[r][c+k]=color
    for _ in range(rng.randrange(4)):grid=_rotate(grid)
    return grid

def generate(seed, settings, demos=2, queries=4):
    direction=_setting(settings)
    for value,lo,hi,label in [(seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')]:
        if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{label} out of range')
    train=[sample(seed,i,'train') for i in range(demos)]
    bank=[sample(seed,i,'test') for i in range(4)]
    _rng(seed,'private-query-presentation').shuffle(bank)
    pairs=lambda grids:[{'input':g,'output':solve(g,direction)} for g in grids]
    return {'train':pairs(train),'test':pairs(bank[:queries]),'program_solution':program(settings)}
