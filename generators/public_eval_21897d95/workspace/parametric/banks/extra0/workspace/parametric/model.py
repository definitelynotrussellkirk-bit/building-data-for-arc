"""Room-to-room color transfer encoded by T arrows and an optional L rotation cue."""
from __future__ import annotations
from collections import Counter
import copy
import random

GENERATOR_ID=TASK_ID='public_eval_21897d95'
RULE_TASK_ID='ee_21897d95'
VERSION='1.0.0'
SUMMARY='Erase T arrows, transfer payload/source colors to pointed rooms, then obey an optional L rotation cue.'
AXES={'payload_mode':['payload','source_only']}
INVARIANTS=['solid colored rooms','color-1 T arrows','target room beyond each stem','optional five-cell L rotation cue']
D4=((-1,0),(0,1),(1,0),(0,-1))
DIRS={'up':(-1,0),'right':(0,1),'down':(1,0),'left':(0,-1)}


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def validate_grid(grid):
    if type(grid) is not list or not 3<=len(grid)<=30 or type(grid[0]) is not list or not 3<=len(grid[0])<=30:
        raise ValueError('grid must be a 3..30 rectangle')
    w=len(grid[0])
    if any(type(row) is not list or len(row)!=w or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('grid must contain exact integer colors 0..9')
    return grid


def _components(grid,color,excluded=frozenset()):
    h,w=len(grid),len(grid[0]);seen=set();result=[]
    for r in range(h):
        for c in range(w):
            if (r,c) in excluded or (r,c) in seen or grid[r][c]!=color:continue
            stack=[(r,c)];seen.add((r,c));cells=[]
            while stack:
                p=stack.pop();cells.append(p)
                for dr,dc in D4:
                    q=(p[0]+dr,p[1]+dc)
                    if 0<=q[0]<h and 0<=q[1]<w and q not in excluded and q not in seen and grid[q[0]][q[1]]==color:
                        seen.add(q);stack.append(q)
            result.append(cells)
    return result


def _adjacent_counts(grid,cells):
    h,w=len(grid),len(grid[0]);cells=set(cells);counts=Counter()
    for r,c in cells:
        for dr,dc in D4:
            q=(r+dr,c+dc)
            if 0<=q[0]<h and 0<=q[1]<w and q not in cells and grid[q[0]][q[1]]!=1:
                counts[grid[q[0]][q[1]]]+=1
    return counts


def _candidate(grid,center,bar,direction):
    h,w=len(grid),len(grid[0]);dr,dc=DIRS[direction]
    stem=(center[0]+dr,center[1]+dc);target=(center[0]+2*dr,center[1]+2*dc)
    if not (0<=stem[0]<h and 0<=stem[1]<w and 0<=target[0]<h and 0<=target[1]<w):return None
    if grid[stem[0]][stem[1]]!=1 or grid[target[0]][target[1]]==1:return None
    cells=set(bar+[stem]);counts=_adjacent_counts(grid,cells)
    if not counts:return None
    ranked=counts.most_common()
    if len(ranked)>1 and ranked[0][1]==ranked[1][1]:return None
    source=ranked[0][0];target_color=grid[target[0]][target[1]]
    if target_color==source:return None
    return {'center':center,'stem':stem,'direction':direction,'delta':(dr,dc),'payload':grid[center[0]][center[1]],
            'source':source,'target':target_color,'target_seed':target,'cells':tuple(sorted(cells)),'score':ranked[0][1]}


def detect_arrows(grid):
    validate_grid(grid);h,w=len(grid),len(grid[0]);raw=[]
    for r in range(1,h-1):
        for c in range(w):
            if grid[r-1][c]==1 and grid[r+1][c]==1:
                bar=[(r-1,c),(r,c),(r+1,c)]
                for direction in ('left','right'):
                    item=_candidate(grid,(r,c),bar,direction)
                    if item:raw.append(item)
    for r in range(h):
        for c in range(1,w-1):
            if grid[r][c-1]==1 and grid[r][c+1]==1:
                bar=[(r,c-1),(r,c),(r,c+1)]
                for direction in ('up','down'):
                    item=_candidate(grid,(r,c),bar,direction)
                    if item:raw.append(item)
    chosen=[]
    for item in sorted(raw,key=lambda a:(-a['score'],a['center'],a['direction'])):
        cells=set(item['cells'])
        if any(cells==set(other['cells']) or cells&set(other['cells']) for other in chosen):continue
        chosen.append(item)
    chosen.sort(key=lambda a:a['center'])
    return chosen


def _bbox(cells):
    return (min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells))


def find_rotation_cue(grid,arrows):
    arrow_cells=set(p for a in arrows for p in a['cells']);h,w=len(grid),len(grid[0]);candidates=[]
    for color in range(10):
        if color==1:continue
        for component in _components(grid,color,arrow_cells):
            if len(component)!=5:continue
            r0,c0,r1,c1=_bbox(component)
            if (r1-r0,c1-c0)!=(2,2):continue
            cells=set(component)
            degrees={p:sum((p[0]+dr,p[1]+dc) in cells for dr,dc in D4) for p in component}
            endpoints=[p for p,d in degrees.items() if d==1]
            if len(endpoints)!=2:continue
            corners=[]
            for p in component:
                vectors=[(e[0]-p[0],e[1]-p[1]) for e in endpoints]
                if (all(abs(dr)+abs(dc)==2 and (dr==0 or dc==0) for dr,dc in vectors)
                        and any(dr==0 for dr,dc in vectors) and any(dc==0 for dr,dc in vectors)):
                    corners.append((p,vectors))
            if len(corners)!=1:continue
            corner,vectors=corners[0];counts=Counter()
            for r,c in cells:
                for dr,dc in D4:
                    q=(r+dr,c+dc)
                    if 0<=q[0]<h and 0<=q[1]<w and q not in cells and q not in arrow_cells:
                        value=grid[q[0]][q[1]]
                        if value not in (1,color):counts[value]+=1
            if not counts:continue
            hvec=next(v for v in vectors if v[1]!=0)
            candidates.append({'color':color,'cells':tuple(sorted(cells)),'corner':corner,'vectors':tuple(vectors),
                               'background':counts.most_common(1)[0][0],'turn':'ccw' if hvec[1]<0 else 'cw'})
    return candidates[0] if candidates else None


def analyze(grid):
    validate_grid(grid);arrows=detect_arrows(grid);cue=find_rotation_cue(grid,arrows)
    return {'shape':(len(grid),len(grid[0])),'arrows':copy.deepcopy(arrows),'rotation_cue':copy.deepcopy(cue)}


def _flood(grid,seed):
    h,w=len(grid),len(grid[0]);color=grid[seed[0]][seed[1]];seen={seed};stack=[seed];cells=[]
    while stack:
        p=stack.pop();cells.append(p)
        for dr,dc in D4:
            q=(p[0]+dr,p[1]+dc)
            if 0<=q[0]<h and 0<=q[1]<w and q not in seen and grid[q[0]][q[1]]==color:
                seen.add(q);stack.append(q)
    return cells


def _rotate_cw(grid):return [list(row) for row in zip(*grid[::-1])]
def _rotate_ccw(grid):return [list(row) for row in zip(*grid)][::-1]


def solve(grid,payload_mode='payload'):
    if payload_mode not in ('payload','source_only'):raise ValueError('payload_mode must be payload or source_only')
    data=analyze(grid);arrows=data['arrows'];cue=data['rotation_cue'];clean=[row[:] for row in grid]
    if cue:
        for r,c in cue['cells']:clean[r][c]=cue['background']
    for arrow in arrows:
        for r,c in arrow['cells']:clean[r][c]=arrow['source']
    base=[row[:] for row in clean];out=[row[:] for row in clean]
    for arrow in arrows:
        paint=arrow['source'] if payload_mode=='source_only' or arrow['payload']==1 else arrow['payload']
        for r,c in _flood(base,arrow['target_seed']):out[r][c]=paint
    if cue:out=_rotate_ccw(out) if cue['turn']=='ccw' else _rotate_cw(out)
    return out


def _fill(grid,box,color):
    r0,c0,r1,c1=box
    for r in range(r0,r1+1):
        for c in range(c0,c1+1):grid[r][c]=color


def _place_arrow(grid,center,direction,payload):
    r,c=center;dr,dc=DIRS[direction]
    if direction in ('left','right'):bar=((r-1,c),(r,c),(r+1,c))
    else:bar=((r,c-1),(r,c),(r,c+1))
    for rr,cc in bar:grid[rr][cc]=1
    grid[r+dr][c+dc]=1;grid[r][c]=payload


def _place_cue(grid,corner,hdir,color):
    r,c=corner
    for k in range(3):grid[r][c+k*hdir]=color
    for k in range(1,3):grid[r+k][c]=color


def scene(seed,index,*,query=False):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    rng=random.Random(f'room-arrows-v1|{seed}|{index}|{query}')
    h=16+2*((seed+index)%6);w=20+2*((3*seed+index)%6)
    h=min(h,26);w=min(w,30);split=h//2
    edge=(index%4==0);c1=max(6,w//3);c2=w-2 if edge else max(c1+6,(2*w)//3)
    palette=[0,2,3,4,5,6,7,8,9];rng.shuffle(palette);colors=palette[:6]
    grid=[[0]*w for _ in range(h)]
    boxes=((0,0,split-1,c1-1),(0,c1,split-1,c2-1),(0,c2,split-1,w-1),
           (split,0,h-1,c1-1),(split,c1,h-1,c2-1),(split,c2,h-1,w-1))
    for box,color in zip(boxes,colors):_fill(grid,box,color)
    arrows=[]
    # top-left -> top-middle
    arrows.append(((max(2,split//3),c1-2),'right',1))
    # top-middle -> top-right, explicit payload
    arrows.append(((max(3,2*split//3),c2-2),'right',colors[3]))
    # bottom-left -> top-left
    arrows.append(((split+1,max(2,c1//2)),'up',1))
    # bottom-middle -> bottom-left, explicit payload
    arrows.append(((min(h-3,split+3),c1+1),'left',colors[2]))
    if edge:
        # Two-cell-wide edge room: the center lies on the right border.
        arrows.append(((max(2,split//2),w-1),'left',colors[4]))
    else:
        arrows.append(((split+1,min(w-3,c2+(w-c2)//2)),'up',1))
    for center,direction,payload in arrows:_place_arrow(grid,center,direction,payload)
    if (seed+index)%3!=0:
        # Put a removable L in the spacious top-left room, away from arrows.
        leftward=(seed+index)%2==0
        corner=(split-4,c1-3 if leftward else 2)
        _place_cue(grid,corner,-1 if leftward else 1,colors[5])
    errors=self_check(grid)
    if errors:raise AssertionError('invalid generated room scene: '+','.join(errors))
    return grid


def generate(seed,sample_index,difficulty=None):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    return scene(seed,sample_index,query=False)


def self_check(grid):
    errors=[]
    try:
        data=analyze(grid)
        if len(data['arrows'])<4:errors.append('fewer than four arrows')
        if sum(a['payload']!=1 for a in data['arrows'])<2:errors.append('explicit payloads missing')
        if not solve(grid):errors.append('empty output')
    except Exception as exc:errors.append(str(exc))
    return errors


def policy_outputs(grid):
    return {'payload':solve(grid,'payload'),'source_only':solve(grid,'source_only'),
            'identity':[row[:] for row in grid]}
