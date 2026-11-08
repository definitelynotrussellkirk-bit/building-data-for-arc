"""195c6913: read swatch sequence and trace alternating horizontal/vertical rays.

The two large terrain colors are not fixed palette values. The top-left cell
identifies wall; the modal remaining color is corridor. Detached 2x2 swatches
encode the repeated sequence in reading order and a final collision color.
No official grids or answers are embedded or imported.
"""
from __future__ import annotations
RULE_TASK_ID = 'ee_195c6913'
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import random

TASK_ID = GENERATOR_ID = 'public_eval_195c6913'
VERSION = '1.0.0'
SUMMARY = 'Decode a color sequence, follow corridor turns, and mark wall collisions.'


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def check_grid(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
        or not 1 <= len(g[0]) <= 30 or any(type(row) is not list or len(row)!=len(g[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('Expected rectangular 1..30 exact-integer color grid')


def components(g, bg):
    seen=set(); result=[]
    for r,row in enumerate(g):
        for c,color in enumerate(row):
            if color==bg or (r,c) in seen: continue
            todo=[(r,c)]; seen.add((r,c)); cells=[]
            while todo:
                x,y=todo.pop(); cells.append((x,y))
                for a,b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0<=a<len(g) and 0<=b<len(g[0]) and (a,b) not in seen and g[a][b]==color:
                        seen.add((a,b)); todo.append((a,b))
            result.append((color,sorted(cells)))
    return result


def parse(g):
    check_grid(g); bg=g[0][0]
    counts=Counter(v for row in g for v in row if v!=bg)
    if not counts: raise ValueError('Missing corridor')
    road=min(counts, key=lambda c:(-counts[c],c))
    swatches=[]
    for color,cells in components(g,bg):
        rs=[p[0] for p in cells]; cs=[p[1] for p in cells]
        if color!=road and len(cells)==4 and max(rs)-min(rs)==1 and max(cs)-min(cs)==1:
            swatches.append((min(rs),min(cs),color,cells))
    swatches.sort()
    if not 3<=len(swatches)<=7: raise ValueError('Need sequence swatches and one collision swatch')
    pattern=[s[2] for s in swatches[:-1]]; stop=swatches[-1][2]
    if stop in pattern: raise ValueError('Collision color must differ from sequence')
    starts=[(r,0) for r,row in enumerate(g) if row[0]==pattern[0]]
    if not starts: raise ValueError('Missing left-edge origin')
    return {'wall':bg,'road':road,'pattern':pattern,'stop':stop,'starts':starts,
            'swatches':[p for s in swatches for p in s[3]]}


def trace(g, start, *, road, wall, turn='north', pivot_back=0, stop_first=False):
    """Input-dependent intermediate: ordered walkable coordinates and collisions.

    A collision marks the blocked forward cell, then pivots at the last free
    cell. A blocked new direction or an out-of-canvas continuation terminates.
    The immutable original terrain is used, not previously rendered colors.
    """
    if turn not in ('north','south'): raise ValueError('Unknown turn direction')
    r,c=start; heading=0; step=-1 if turn=='north' else 1
    path=[(r,c)]; bumps=[]
    for _ in range(2*(len(g)+len(g[0]))):
        nr,nc=(r,c+1) if heading==0 else (r+step,c)
        if not (0<=nr<len(g) and 0<=nc<len(g[0])): break
        if g[nr][nc]==road:
            r,c=nr,nc; path.append((r,c)); continue
        if g[nr][nc]==wall: bumps.append((nr,nc))
        if stop_first: break
        if pivot_back and heading==0 and c>0: c-=1
        heading=1-heading
        nr,nc=(r,c+1) if heading==0 else (r+step,c)
        if not (0<=nr<len(g) and 0<=nc<len(g[0]) and g[nr][nc]==road): break
        r,c=nr,nc; path.append((r,c))
    else:
        raise ValueError('Trace exceeded monotone path bound')
    return path,bumps


def solve(g, turn='north', *, rival=None):
    facts=parse(g); out=deepcopy(g); pat=facts['pattern'][:]
    if turn not in ('north','south'): raise ValueError('Unknown turn direction')
    if rival=='opposite_turn': turn='south' if turn=='north' else 'north'
    if rival=='reverse_sequence': pat=pat[::-1]
    if rival=='deduplicate_sequence': pat=list(dict.fromkeys(pat))
    if rival=='first_color_only': pat=pat[:1]
    if rival!='keep_legend':
        for r,c in facts['swatches']: out[r][c]=facts['wall']
    for start in facts['starts']:
        path,bumps=trace(g,start,road=facts['road'],wall=facts['wall'],turn=turn,
                         pivot_back=int(rival=='early_pivot'),stop_first=rival=='stop_first')
        phase=1 if rival=='phase_plus_one' else 0; prevdir=(0,1)
        for i,(r,c) in enumerate(path):
            if rival=='reset_at_turn' and i:
                direction=(r-path[i-1][0],c-path[i-1][1])
                if direction!=prevdir: phase=0
                prevdir=direction
            out[r][c]=pat[phase%len(pat)]; phase+=1
        if rival!='omit_collision':
            for r,c in bumps: out[r][c]=facts['stop']
    return out


RIVALS=('opposite_turn','stop_first','reverse_sequence','deduplicate_sequence',
        'first_color_only','keep_legend','phase_plus_one','reset_at_turn',
        'early_pivot','omit_collision')


def rng_for(seed,slot,attempt=0):
    payload=f'{TASK_ID}:{VERSION}:{seed}:{slot}:{attempt}'.encode()
    return random.Random(int.from_bytes(sha256(payload).digest(),'big'))


def scene(seed,slot,attempt=0,stress=False):
    rng=rng_for(seed,slot,attempt)
    h=30 if stress else rng.randint(21,29); w=30 if stress else rng.randint(20,29)
    bg,road,stop,a,b,c=rng.sample(range(10),6)
    # Repeated swatches are intentional and must not be deduplicated.
    pattern=([a,a,b] if slot%2==0 else [a,b,c,a]) if slot<2 else rng.choice(([a,b],[a,a,b],[a,b,c,a],[a,a,a,b]))
    g=[[bg]*w for _ in range(h)]
    lanes=2 if stress or (h>=26 and rng.random()<0.6) else 1
    if lanes==2:
        regions=[(5,13),(18,h-4)] if stress else [(5,12),(16,h-4)]
    else: regions=[(5,h-4)]
    starts=[]
    for lo,hi in regions:
        center=(lo+hi)//2
        slope=rng.choice([4,5,6]) if lanes==2 else rng.choice([2,3,4])
        span=rng.randint(15,17) if stress else rng.randint(6,11)
        for r in range(lo,hi+1):
            d=abs(r-center)
            left=min(w-1,max(0,d*slope+rng.randint(-1,1))) if d else 0
            right=min(w-1,left+span+rng.randint(-1,1))
            for col in range(left,right+1): g[r][col]=road
        starts.append((center,0)); g[center][0]=pattern[0]
    top=rng.choice([1,2]); left=rng.choice([1,2])
    for j,color in enumerate(pattern):
        for r in (top,top+1):
            for col in (left+3*j,left+3*j+1): g[r][col]=color
    for r in (h-3,h-2):
        for col in (w-4,w-3): g[r][col]=stop
    return g


@lru_cache(maxsize=64)
def bank(seed):
    integer(seed,0,2**63-1,'seed')
    for attempt in range(128):
        grids=[scene(seed,slot,attempt,stress=slot==9) for slot in range(10)]
        if len({str(g) for g in grids})!=10: continue
        # Keep disjoint source paths; cross-path overwrite is not part of this grammar.
        lawful=True
        for g in grids:
            facts=parse(g)
            for turn in ('north','south'):
                used=set()
                for start in facts['starts']:
                    path,bumps=trace(g,start,road=facts['road'],wall=facts['wall'],turn=turn)
                    pts=set(path+bumps)
                    if used & pts or len(bumps)<1: lawful=False
                    used.update(pts)
        if not lawful: continue
        # Enforce distinguishing teaching for BOTH settings before selecting a setting.
        for turn in ('north','south'):
            demos=[solve(g,turn) for g in grids[:2]]
            for rival in RIVALS:
                if all(solve(g,turn,rival=rival)==y for g,y in zip(grids[:2],demos)):
                    if any(solve(g,turn,rival=rival)!=solve(g,turn) for g in grids[6:]):
                        lawful=False; break
            if not lawful: break
        if lawful: return tuple(grids)
    raise ValueError('Bounded constructive lesson sampler exhausted 128 attempts')


def generate(seed, sample_index, *, difficulty=None, **overrides):
    integer(seed,0,2**63-1,'seed'); integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'): raise ValueError('Unknown difficulty')
    if overrides: raise ValueError('Unknown controls: '+','.join(sorted(overrides)))
    return deepcopy(scene(seed,sample_index,stress=difficulty=='hard' or sample_index%10==9))


def self_check(grid, *, difficulty=None, meta=None):
    try: parse(grid)
    except (ValueError,TypeError,IndexError) as exc: return [str(exc)]
    return []
