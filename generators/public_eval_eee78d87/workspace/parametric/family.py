"""Recovered motif -> phase-aligned two-dimensional texture.

Finite rival checks are curriculum constraints, not a uniqueness proof.
All randomness is private, keyed by the episode seed and independent of setting.
"""
from __future__ import annotations
from functools import lru_cache
import hashlib
import random

SETTINGS=('translation','alternating_mirror')
RIVALS=('other_setting','no_crop','no_center','all_highlight','wrong_phase',
        'flip_lr_once','flip_ud_once','fixed_three')


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an integer in {lo}..{hi}; booleans forbidden')
    return value


def setting(value):
    if type(value) is not dict or set(value)!={'tiling'} or type(value['tiling']) is not str or value['tiling'] not in SETTINGS:
        raise ValueError('Expected exactly tiling=translation|alternating_mirror')
    return value['tiling']


def checked_grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=13 or type(grid[0]) is not list
        or not 1<=len(grid[0])<=13 or any(type(row) is not list or len(row)!=len(grid[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected rectangular exact-integer 1..13 grid')
    return grid


def intermediate(grid):
    checked_grid(grid)
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=7]
    if not cells:raise ValueError('A non-orange motif is required')
    r0=min(r for r,c in cells);r1=max(r for r,c in cells)
    c0=min(c for r,c in cells);c1=max(c for r,c in cells)
    return {'bbox':[r0,c0,r1,c1],'period':[r1-r0+1,c1-c0+1],
            'center_origin':[len(grid)+2-(r1-r0+1),len(grid[0])+2-(c1-c0+1)]}


def solve(grid,tiling,*,variant=None):
    if tiling not in SETTINGS:raise ValueError('Unknown tiling')
    info=intermediate(grid);r0,c0,r1,c1=info['bbox']
    motif=[[v!=7 for v in row[c0:c1+1]] for row in grid[r0:r1+1]]
    if variant=='no_crop':motif=[[v!=7 for v in row] for row in grid]
    if variant=='flip_lr_once':motif=[row[::-1] for row in motif]
    if variant=='flip_ud_once':motif=motif[::-1]
    if variant=='fixed_three':motif=[[motif[r%len(motif)][c%len(motif[0])] for c in range(3)] for r in range(3)]
    mh,mw=len(motif),len(motif[0]);H,W=2*len(grid)+4,2*len(grid[0])+4
    sr,sc=H//2-mh,W//2-mw
    origin_r,origin_c=(0,0) if variant=='wrong_phase' else (sr,sc)
    out=[]
    for r in range(H):
        row=[]
        for c in range(W):
            dr,dc=r-origin_r,c-origin_c;mr,mc=dr%mh,dc%mw
            if tiling=='alternating_mirror':
                if (dr//mh)%2:mr=mh-1-mr
                if (dc//mw)%2:mc=mw-1-mc
            highlight=sr<=r<sr+2*mh and sc<=c<sc+2*mw
            if variant=='no_center':highlight=False
            if variant=='all_highlight':highlight=True
            row.append((9 if highlight else 0) if motif[mr][mc] else 7)
        out.append(row)
    return out


def rival(grid,tiling,name):
    if name not in RIVALS:raise ValueError('Unknown rival')
    if name=='other_setting':return solve(grid,SETTINGS[1-SETTINGS.index(tiling)])
    return solve(grid,tiling,variant=name)


def rng(seed,label):
    return random.Random(int.from_bytes(hashlib.sha256(f'eee78d87:{seed}:{label}'.encode()).digest(),'big'))


def make_grid(seed,label,shape):
    H,W,mh,mw=shape;randomizer=rng(seed,label)
    # Every edge is supported; reject symmetric masks, which conceal reflections.
    for _ in range(128):
        mask=[[randomizer.random()<0.48 for c in range(mw)] for r in range(mh)]
        for r,c in [(0,randomizer.randrange(mw)),(mh-1,randomizer.randrange(mw)),
                    (randomizer.randrange(mh),0),(randomizer.randrange(mh),mw-1)]:mask[r][c]=True
        if mask==mask[::-1] or mask==[row[::-1] for row in mask]:continue
        break
    else:raise ValueError('Failed to construct asymmetric motif within 128 trials')
    r0=randomizer.randrange(H-mh+1);c0=randomizer.randrange(W-mw+1)
    palette=randomizer.sample([1,2,3,4,5,6,8],randomizer.randint(1,3))
    grid=[[7]*W for _ in range(H)]
    for r in range(mh):
        for c in range(mw):
            if mask[r][c]:grid[r0+r][c0+c]=randomizer.choice(palette)
    return grid


@lru_cache(maxsize=64)
def input_bank(seed):
    integer(seed,0,2**63-1,'seed')
    demos=[(6,7,3,4),(7,6,4,3),(8,9,3,5),(9,8,5,3),(10,11,6,7),(11,10,7,6)]
    queries=[(6,6,3,3),(9,11,4,6),(11,9,6,4),(13,13,10,10)]
    for attempt in range(64):
        train=[make_grid(seed,f'demo:{attempt}:{i}',shape) for i,shape in enumerate(demos)]
        # Enforce a demonstrated difference, not just disagreement on hidden queries.
        if all(any(rival(g,s,name)!=solve(g,s) for g in train[:2]) for s in SETTINGS for name in RIVALS):break
    else:raise ValueError('No two-demo teaching certificate within 64 constructions')
    test=[make_grid(seed,f'query:{i}',shape) for i,shape in enumerate(queries)]
    rng(seed,'presentation').shuffle(test)
    freeze=lambda gs:tuple(tuple(tuple(row) for row in g) for g in gs)
    return freeze(train),freeze(test)


def grids(seed):
    train,test=input_bank(seed)
    return [[list(row) for row in g] for g in train],[[list(row) for row in g] for g in test]
