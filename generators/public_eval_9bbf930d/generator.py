"""Move left-edge magenta markers through same-color rail corridors.

The active guide color is a state derived from the walls crossed so far.
Canonical routing refreshes it inside a new matching pair of rails. The
parametric entry variant freezes it at launch. The sampler uses no gold data.
"""
from __future__ import annotations
RULE_TASK_ID = 'ee_9bbf930d'
import hashlib
import random
from typing import Any

GENERATOR_ID = TASK_ID = 'public_eval_9bbf930d'
VERSION = '1.0.0'
SUMMARY = 'Trace background corridors; active rail colors decide turns versus stops.'
WALL_COLORS = (0,1,2,3,4,5,8,9)


def validate_grid(grid: Any) -> None:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError('Expected a 1..30 rectangular integer grid')
    width=len(grid[0])
    if any(type(row) is not list or len(row)!=width or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('Expected exact integer colors 0..9')


def launches(grid, *, rival=None):
    h,w=len(grid),len(grid[0]);found=[]
    for r in range(1,h-1):
        if grid[r][0]!=6:continue
        columns=[2] if rival=='fixed_column2' and w>2 else range(1,w)
        for c in columns:
            if grid[r][c]!=7:break
            a,b=grid[r-1][c],grid[r+1][c]
            if a==b==7:continue
            valid=(a in WALL_COLORS and b in WALL_COLORS and (a==b or rival=='start_every_gap'))
            if valid and not (rival=='ignore_black' and a==0):found.append((r,a))
            break
    return found


def trace(grid, start_row, initial_color, guide_update='local', *, rival=None):
    h,w=len(grid),len(grid[0])
    def at(r,c):return grid[r][c] if 0<=r<h and 0<=c<w else -1
    r,c,dr,dc,color=start_row,0,0,1,initial_color
    visited=set();states=[];turns=0;cycle=False
    for _ in range(32*h*w+1):
        a,b=at(r-dc,c+dr),at(r+dc,c-dr)
        if guide_update=='local' and a==b and a in WALL_COLORS and not (rival=='ignore_black' and a==0):color=a
        state=(r,c,dr,dc,color)
        if state in visited:cycle=True;break
        visited.add(state);states.append(state)
        front=at(r+dr,c+dc)
        if front==7:r+=dr;c+=dc;continue
        can_turn=(front==color or (rival=='turn_any_obstacle' and front in WALL_COLORS))
        if rival=='straight_only' or (rival=='one_turn_only' and turns>=1):can_turn=False
        if can_turn:
            choices=[d for d in ((-dc,dr),(dc,-dr)) if at(r+d[0],c+d[1])==7]
            if len(choices)==1:
                dr,dc=choices[0];turns+=1;continue
        break
    else:cycle=True
    return {'source':(start_row,0),'destination':(r,c),'entry_color':initial_color,
            'final_color':color,'turns':turns,'states':states,'cycle':cycle}


def routes(grid, guide_update='local', *, rival=None):
    validate_grid(grid)
    if guide_update not in ('local','entry'):raise ValueError('guide_update must be local or entry')
    return [trace(grid,r,color,guide_update,rival=rival) for r,color in launches(grid,rival=rival)]


def solve(grid, guide_update='local', *, rival=None):
    validate_grid(grid)
    if guide_update not in ('local','entry'):raise ValueError('guide_update must be local or entry')
    out=[row[:] for row in grid]
    if rival=='identity':return out
    records=routes(grid,guide_update,rival=rival)
    for rec in records:
        r,c=rec['source'];out[r][c]=7
    for rec in records:
        if rival=='erase_sources_only':continue
        targets=[rec['destination']]
        if rival=='paint_full_route':targets=[s[:2] for s in rec['states']]
        for r,c in targets:out[r][c]=6
    return out


def self_check(grid, *, difficulty=None, meta=None):
    try:
        validate_grid(grid)
        if len(grid)<3 or len(grid[0])<4:return ['Corridor canvas too small']
        if any(row[0]!=6 or 6 in row[1:] for row in grid):return ['Input requires one complete left-edge magenta bar and no other magenta']
        for mode in ('local','entry'):
            rr=routes(grid,mode)
            if any(r['cycle'] for r in rr):return ['Cyclic beam route outside sampler grammar']
            if len({r['destination'] for r in rr})!=len(rr):return ['Marker endpoints collide']
            out=solve(grid,mode)
            if sum(v==6 for row in out for v in row)!=len(grid):return ['Markers must be conserved']
        return []
    except (ValueError,TypeError) as exc:return [str(exc)]


def rng_for(seed,*parts):
    raw='|'.join(map(str,(TASK_ID,VERSION,seed,*parts))).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(),'big'))


def _line(a,b):
    dr=(b[0]>a[0])-(b[0]<a[0]);dc=(b[1]>a[1])-(b[1]<a[1])
    if dr and dc:raise ValueError('Polyline segments must be orthogonal')
    length=abs(b[0]-a[0])+abs(b[1]-a[1])
    return [(a[0]+i*dr,a[1]+i*dc) for i in range(length+1)]


def sample_input(rng,height,width,profile=0):
    if not 13<=height<=30 or not 17<=width<=30:raise ValueError('Corridor sampler requires 13..30 by 17..30')
    for _ in range(256):
        start=2+profile%2
        three_turns=profile%2==1 or rng.choice((False,True))
        c1=rng.randint(max(start+6,width//2),width-6)
        odd=list(range(3,height-2,2))
        candidates=[(a,b) for a in odd for b in odd if abs(a-b)>=4]
        r1,r2=rng.choice(candidates)
        a,b=rng.sample(WALL_COLORS,2)
        probe_color=0 if profile%2==0 else rng.choice(WALL_COLORS)
        foreign=rng.choice([v for v in WALL_COLORS if v!=probe_color])
        grid=[[7]*width for _ in range(height)]
        for row in grid:row[0]=6
        # Unequal neighboring rail stubs teach which left-edge cells do not launch.
        previous=None
        for rr in range(0,height,2):
            color=rng.choice([v for v in WALL_COLORS if v!=previous]);previous=color
            end=rng.randint(start+1,c1-3)
            for cc in range(start,end+1):grid[rr][cc]=color
        if three_turns:
            c2=rng.randint(c1+4,width-2)
            end_row=rng.choice((0,height-1))
            vertices=[(r1,start),(r1,c1),(r2,c1),(r2,c2),(end_row,c2)]
        else:
            vertices=[(r1,start),(r1,c1),(r2,c1),(r2,width-1)]
        path=[];offsets=[]
        for i,(v1,v2) in enumerate(zip(vertices,vertices[1:])):
            offsets.append(len(path)-1 if path else 0)
            segment=_line(v1,v2);path.extend(segment if i==0 else segment[1:])
        switch_segment=2 if profile%2 else 1
        seg_len=abs(vertices[switch_segment+1][0]-vertices[switch_segment][0])+abs(vertices[switch_segment+1][1]-vertices[switch_segment][1])
        switch=offsets[switch_segment]+seg_len//2
        occupied=set(path)
        for i,(rr,cc) in enumerate(path):
            color=a if i<switch else b
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                p=(rr+dr,cc+dc)
                if 0<=p[0]<height and 1<=p[1]<width and p not in occupied and p!=(r1,start-1):
                    grid[p[0]][p[1]]=color
        for rr,cc in path:grid[rr][cc]=7
        # A bounded pair of rail gaps tests persistence across unguided space.
        gap_options=list(range(start+2,c1-2))
        for cc in rng.sample(gap_options,min(len(gap_options),rng.randint(0,2))):
            grid[r1-1][cc]=grid[r1+1][cc]=7
        # Separate short corridor: black is a real wall, and a foreign-colored
        # one-sided elbow must STOP, not turn. It is left of the main route.
        block=start+4
        for rr in range(r2-1,r2+2):
            for cc in range(start,block+1):grid[rr][cc]=7
        for cc in (start,start+1):grid[r2-1][cc]=grid[r2+1][cc]=probe_color
        grid[r2][block]=foreign;grid[r2-1][block-1]=foreign
        # Optional foreign end stop, in addition to boundary exits.
        if rng.choice((False,True)):
            rr,cc=path[-1]
            grid[rr][cc]=rng.choice([v for v in WALL_COLORS if v!=b])
        if rng.choice((False,True)):grid.reverse()
        if self_check(grid):continue
        if solve(grid,'local')!=solve(grid,'entry'):
            return grid
    raise RuntimeError('Bounded corridor sampler exhausted 256 attempts')


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(seed) is not int or not 0<=seed<2**63 or type(sample_index) is not int or sample_index<0:
        raise ValueError('seed and sample_index must be exact nonnegative integers')
    if difficulty not in (None,'easy','medium','hard') or overrides:raise ValueError('Unsupported request')
    shape={'easy':(13,17),'medium':(21,25),'hard':(30,30)}.get(difficulty,(19,23))
    grid=sample_input(rng_for(seed,'single',sample_index),*shape,profile=sample_index%2)
    return {'input':grid,'metadata':{'generator_id':TASK_ID,'version':VERSION,'seed':seed,'sample_index':sample_index}}

solve_python=solve
