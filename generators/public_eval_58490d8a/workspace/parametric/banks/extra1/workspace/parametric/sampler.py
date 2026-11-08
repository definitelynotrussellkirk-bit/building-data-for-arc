"""Standalone synthetic input sampler for a legend-directed component-count chart.

Objects are placed without overlap or same-color diagonal merging. Only the chart
contains black; canvas and object colors vary. No answers or original grids are
imported. Native sampler.py is an exact resource copy of this standalone module.
"""
from collections import Counter
import hashlib
import random

TASK_ID='public_eval_58490d8a'
GENERATOR_ID=TASK_ID
RULE_TASK_ID='ee_58490d8a'
VERSION='1.0.0'
SUMMARY='Count external eight-connected objects in a supplied color legend.'
EXAMPLES_NEEDED=2
AXES={}
SHAPES={
 'plus5':[(0,1),(1,0),(1,1),(1,2),(2,1)],
 'diag4':[(i,i) for i in range(4)],
 'box4':[(r,c) for r in range(2) for c in range(2)],
 'box9':[(r,c) for r in range(3) for c in range(3)],
 'L4':[(0,0),(1,0),(2,0),(2,1)],
 'L3':[(0,0),(1,0),(1,1)],
 'line4':[(0,i) for i in range(4)],
 'dot':[(0,0)]}


def transformed(cells,turns,mirror):
    cells=list(cells)
    if mirror:cells=[(r,-c) for r,c in cells]
    for _ in range(turns):cells=[(c,-r) for r,c in cells]
    r0=min(r for r,c in cells);c0=min(c for r,c in cells)
    return [(r-r0,c-c0) for r,c in cells]


def generate(seed,sample_index=0,*,difficulty=None,**overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index<0:
        raise ValueError('exact integer seed and nonnegative sample_index required')
    if difficulty not in (None,'easy','medium','hard') or overrides:
        raise ValueError('unsupported difficulty or override')
    rng=random.Random(int.from_bytes(hashlib.sha256(
        f'{TASK_ID}|{VERSION}|{seed}|{sample_index}'.encode()).digest(),'big'))
    profile=(sample_index-100)%4 if sample_index>=100 else (sample_index+1)%4
    h,w,n=[(22,24,2),(26,28,3),(28,26,3),(30,30,4)][profile]
    if sample_index==0:
        groups=[['plus5','plus5','diag4','box4'],['box9','diag4','diag4'],['L4','box4']]
    elif sample_index==1:
        groups=[['box9','L3','L3','L3'],['box4','diag4','line4'],['plus5','plus5','diag4']]
    elif profile==3:
        groups=[['plus5','plus5','diag4','box4'],['box9','diag4','diag4'],
                ['L4','box4'],['box9','box9','diag4','diag4','diag4']]
    else:
        choices=[['plus5','diag4','box4'],['box4','L4','diag4'],
                 ['box9','plus5','plus5'],['plus5','plus5','box4','box4','box4'],
                 ['L3','dot'],['box9','diag4','diag4','line4']]
        groups=[list(rng.choice(choices)) for _ in range(n)]
    bg=rng.randrange(1,10)
    palette=rng.sample([c for c in range(1,10) if c!=bg],n+1)
    legend=palette[:n];decoy=palette[-1]
    ph=2*n+1;pw=max(9,2*max(map(len,groups))+1)+rng.randrange(3)
    objects=[(color,shape) for color,group in zip(legend,groups) for shape in group]
    objects.extend([(decoy,'box9')]*(2 if profile==3 else 1))
    def starts(size):
        out=list(range(0,size-3,6))
        # Keep large inter-slot gaps, but let a final 4x4 cell reach 30x30's edge.
        if size==30:out[-1]=26
        return out
    slot_grid=[(r,c) for r in starts(h) for c in starts(w)]
    candidates=[(0,0),(0,w-pw),(h-ph,0),(h-ph,w-pw),((h-ph)//2,(w-pw)//2),(2,max(2,(w-pw)//2))]
    viable=[]
    for top,left in candidates:
        slots=[(r,c) for r,c in slot_grid if
               r+3<top-1 or r>top+ph or c+3<left-1 or c>left+pw]
        if len(slots)>=len(objects):viable.append((top,left,slots))
    if not viable:raise ValueError('constructive placement has insufficient separated slots')
    if profile==2 and len(viable)>4:
        top,left,slots=viable[-1]
    else:top,left,slots=rng.choice(viable)
    grid=[[bg]*w for _ in range(h)]
    for r in range(top,top+ph):
        for c in range(left,left+pw):grid[r][c]=0
    rng.shuffle(legend)
    if sample_index==0:
        # The minimum lesson must not accidentally teach numeric color order.
        low,middle,high=sorted(legend)
        legend=[middle,high,low]
    for i,color in enumerate(legend):grid[top+2*i+1][left+1]=color
    rng.shuffle(objects);rng.shuffle(slots)
    for (color,shape),(r,c) in zip(objects,slots):
        cells=transformed(SHAPES[shape],rng.randrange(4),rng.randrange(2))
        hh=max(a for a,b in cells)+1;ww=max(b for a,b in cells)+1
        # Each occupied component remains inside its non-touching 4x4 slot.
        dr=rng.randrange(5-hh);dc=rng.randrange(5-ww)
        if r==26:dr=4-hh
        if c==26:dc=4-ww
        for a,b in cells:grid[r+dr+a][c+dc+b]=color
    return grid


def self_check(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or
        not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0]) for row in grid) or
        any(type(v) is not int or not 0<=v<=9 for row in grid for v in row)):
        return ['invalid grid']
    zeros=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==0]
    if not zeros:return ['missing black chart']
    r0=min(r for r,c in zeros);r1=max(r for r,c in zeros);c0=min(c for r,c in zeros);c1=max(c for r,c in zeros)
    marks=[(r,c,grid[r][c]) for r in range(r0,r1+1) for c in range(c0,c1+1) if grid[r][c]!=0]
    if not marks or len({r for r,c,v in marks})!=len(marks) or len({v for r,c,v in marks})!=len(marks):
        return ['chart needs one seed on each distinct color row']
    return []
