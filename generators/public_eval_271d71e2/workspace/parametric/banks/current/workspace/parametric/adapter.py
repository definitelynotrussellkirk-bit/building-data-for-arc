"""Fuel-limited sliding and longest-actual-move selection; no original-grid lookup.

All native resources are adjacent. Python labels are independent claims, verified
by the protected Racket worker before owner acceptance. Geometry is setting-neutral.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
PARAMETERS={'motion_policy':['all_moves','longest_move']}
DEFAULT={'motion_policy':'all_moves'}
RIVALS=('all_moves','max_gap','max_fuel','min_remaining','max_final_orange','largest_box','first','last','shortest_move')

def _setting(settings):
    if type(settings) is not dict or set(settings)!=set(PARAMETERS) or settings.get('motion_policy') not in PARAMETERS['motion_policy']:
        raise ValueError('settings must name exactly one declared motion_policy')
    return settings['motion_policy']

def program(settings):
    policy=_setting(settings);source=(HERE/'canonical.rkt').read_text()
    return source if policy=='all_moves' else source.replace('(define output-policy "all_moves")',f'(define output-policy "{policy}")',1)

def rival_programs():
    source=program(DEFAULT)
    return {name:source.replace('(define output-policy "all_moves")',f'(define output-policy "{name}")',1) for name in RIVALS}

def _grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30
        or any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected rectangular exact-integer color grid, dimensions 1..30')
    return tuple(map(tuple,grid))

def _key(p,dr,dc):
    r,c=p
    return (r,c) if dr==-1 else (-r,-c) if dr==1 else (-c,r) if dc==1 else (c,-r)

@lru_cache(maxsize=2048)
def _analyze(grid):
    H,W=len(grid),len(grid[0]);black={(r,c) for r in range(H) for c in range(W) if grid[r][c]==0};frames=[]
    def value(r,c):return grid[r][c] if 0<=r<H and 0<=c<W else -1
    while black:
        seed=min(black);black.remove(seed);todo=[seed];cells=[seed]
        while todo:
            r,c=todo.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in black:black.remove(p);todo.append(p);cells.append(p)
        r1,r2=min(r for r,c in cells),max(r for r,c in cells);c1,c2=min(c for r,c in cells),max(c for r,c in cells)
        if r2-r1<2 or c2-c1<2:continue
        border={(r,c) for r in range(r1,r2+1) for c in range(c1,c2+1) if r in (r1,r2) or c in (c1,c2)}
        if set(cells)!=border:raise ValueError('black component is not a rectangular border')
        if any(grid[r][c] not in (5,7) for r in range(r1+1,r2) for c in range(c1+1,c2)):
            raise ValueError('fuel interior must contain gray/orange cells')
        candidates=[]
        for dr,dc in [(-1,0),(0,1),(1,0),(0,-1)]:
            rail=([(r1-1,c) for c in range(c1,c2+1)] if dr==-1 else [(r2+1,c) for c in range(c1,c2+1)] if dr==1 else
                  [(r,c1-1) for r in range(r1,r2+1)] if dc==-1 else [(r,c2+1) for r in range(r1,r2+1)])
            if all(value(r,c)==9 for r,c in rail):candidates.append((dr,dc,rail))
        if len(candidates)!=1:raise ValueError('expected one attached mobile maroon rail')
        dr,dc,rail=candidates[0]
        gap=next((n for n in range(1,31) if all(value(r+dr*n,c+dc*n)==9 for r,c in rail)),None)
        if gap is None:raise ValueError('missing parallel fixed rail')
        gray=sorted([(r,c) for r in range(r1+1,r2) for c in range(c1+1,c2) if grid[r][c]==5],key=lambda p:_key(p,dr,dc))
        frames.append({'box':[r1,c1,r2,c2],'border':sorted(border),'rail':rail,'direction':[dr,dc],
                       'gap':gap,'fuel':len(gray),'gray':gray,'distance':min(gap,len(gray)),'area':(r2-r1-1)*(c2-c1-1)})
    if not frames:raise ValueError('no framed fuel boxes')
    return frames

def analyze(grid):return deepcopy(_analyze(_grid(grid)))

def predict(grid,policy='all_moves'):
    if policy not in RIVALS+('longest_move',):raise ValueError('unknown policy')
    frames=_analyze(_grid(grid));out=deepcopy(grid)
    keys={'max_gap':lambda f:f['gap'],'max_fuel':lambda f:f['fuel'],'min_remaining':lambda f:f['distance']-f['fuel'],
          'max_final_orange':lambda f:f['area']-f['fuel']+f['distance'],'largest_box':lambda f:(f['box'][2]-f['box'][0]+1)*(f['box'][3]-f['box'][1]+1),
          'shortest_move':lambda f:-f['distance']}
    winner=frames[0] if policy=='first' else frames[-1] if policy=='last' else max(frames,key=keys.get(policy,lambda f:f['distance']))
    for f in frames:
        r1,c1,r2,c2=f['box']
        for r in range(r1,r2+1):
            for c in range(c1,c2+1):out[r][c]=6
        for r,c in f['rail']:out[r][c]=6
    for f in frames:
        r1,c1,r2,c2=f['box'];dr,dc=f['direction'];n=f['distance'];spent=set(f['gray'][:n])
        for r in range(r1,r2+1):
            for c in range(c1,c2+1):
                v=grid[r][c]
                out[r+dr*n][c+dc*n]=8 if policy!='all_moves' and f==winner and v==0 else 7 if (r,c) in spent else v
        for r,c in f['rail']:out[r+dr*n][c+dc*n]=9
    return out

def rotate(g,k):
    for _ in range(k%4):g=[list(row) for row in zip(*g[::-1])]
    return g

def _scene(seed,index,attempt=0):
    rng=random.Random(f'271d71e2:geometry:v1:{seed}:{index}:{attempt}')
    large=index==9
    heights=[6,7,7,7] if large else ([rng.randint(4,6) for _ in range(3+(index%2))])
    H=sum(heights)+len(heights)-1;W=30 if large else rng.randint(23,29)
    # Largest rail gap and fuel count deliberately belong to different nonwinners.
    distance=11 if large else rng.randint(4,8)
    fuel_stop=bool(index%2)
    winner_gap=distance+rng.randint(1,3) if fuel_stop else distance
    winner_fuel=distance if fuel_stop else distance+rng.randint(1,4)
    rows=[('winner',winner_gap,winner_fuel),('gap',rng.randint(max(12,winner_gap+1),16),rng.randint(1,3)),
          ('fuel',rng.randint(1,min(6,distance-1)),rng.randint(max(14,winner_fuel+1),18))]
    if len(heights)==4:rows.append(('other',rng.randint(8,12),0 if index%3==0 else rng.randint(1,3)))
    rng.shuffle(rows);g=[[6]*W for _ in range(H)];r0=0
    for slot,(hh,(role,gap,fuel)) in enumerate(zip(heights,rows)):
        iw=max(4,(fuel+hh-3)//(hh-2));iw=rng.randint(iw,min(10,W-gap-3));fw=iw+2
        right=bool(slot%2) if large else bool(rng.randrange(2));dc=1 if right else -1
        railc=W-1-gap if right else gap;c0=railc-fw if right else railc+1
        fixed=W-1 if right else 0
        for r in range(r0,r0+hh):
            g[r][railc]=g[r][fixed]=9
            for c in range(c0,c0+fw):g[r][c]=0
        inside=sorted([(r,c) for r in range(r0+1,r0+hh-1) for c in range(c0+1,c0+fw-1)],key=lambda p:_key(p,0,dc))
        for j,(r,c) in enumerate(inside):g[r][c]=7 if j<len(inside)-fuel else 5
        r0+=hh+1
    g=rotate(g,rng.randrange(4));f=_analyze(_grid(g));dist=[x['distance'] for x in f]
    if dist.count(max(dist))!=1:raise ValueError('construction needs unique actual-move winner')
    return g

@lru_cache(maxsize=128)
def _bank(seed):
    bank=[];seen=set();survivors=set(RIVALS)-{'all_moves'}
    for index in range(10):
        for attempt in range(120):
            g=_scene(seed,index,attempt);key=_grid(g)
            if key in seen:continue
            rejected={name for name in survivors if predict(g,name)!=predict(g,'longest_move')}
            if index==1 and survivors-rejected:continue
            bank.append(g);seen.add(key)
            if index<2:survivors-=rejected
            break
        else:raise ValueError(f'no distinguishing unique scene at slot {index}')
    if survivors:raise ValueError(f'two-demo survivors {sorted(survivors)}')
    return tuple(bank)

def generate(seed,settings,demos=3,queries=4):
    policy=_setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('integer seed, demos 2..6 and queries 1..4 required')
    bank=_bank(seed);perm=list(range(4));random.Random(f'271d71e2:presentation:{seed}').shuffle(perm)
    def pair(i):
        g=deepcopy(bank[i]);return {'input':g,'output':predict(g,policy)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(6+i) for i in perm[:queries]],
            'program_solution':program(settings),'private':{'seed':seed,'settings':deepcopy(settings),'query_permutation':perm}}

def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
