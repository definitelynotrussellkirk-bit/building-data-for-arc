"""Mask-controlled tile substitution, then topology of the assembled mosaic.

Only adjacent resources are read. Official examples are never generation data.
Labels are deterministic Python claims checked by protected Racket independently.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
PARAMETERS={'pocket_policy':['repeat','largest_enclosed']}
DEFAULT={'pocket_policy':'repeat'}
RIVALS=('repeat','all_enclosed','smallest_enclosed','first_enclosed',
        'last_enclosed','tile_holes','mask_area','mask_area_last')


def _setting(settings):
    if (type(settings) is not dict or set(settings)!=set(PARAMETERS)
            or type(settings['pocket_policy']) is not str
            or settings['pocket_policy'] not in PARAMETERS['pocket_policy']):
        raise ValueError('settings must name exactly one declared pocket_policy')
    return settings['pocket_policy']


def program(settings):
    policy=_setting(settings);source=(HERE/'canonical.rkt').read_text()
    return source if policy=='repeat' else source.replace(
        '(define output-policy "repeat")',f'(define output-policy "{policy}")',1)


def rival_programs():
    source=program(DEFAULT)
    return {name:source.replace('(define output-policy "repeat")',
            f'(define output-policy "{name}")',1) for name in RIVALS}


def _grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
            or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0])
            or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected rectangular exact-integer color grid within 30x30')
    return tuple(tuple(row) for row in grid)


def _components(points, diagonal=False):
    left=set(points);result=[]
    directions=tuple((a,b) for a in (-1,0,1) for b in (-1,0,1)
                     if (a or b) and (diagonal or abs(a)+abs(b)==1))
    while left:
        first=min(left);left.remove(first);todo=[first];part={first}
        while todo:
            r,c=todo.pop()
            for dr,dc in directions:
                p=(r+dr,c+dc)
                if p in left:
                    left.remove(p);part.add(p);todo.append(p)
        result.append(sorted(part))
    return result


def _enclosed(grid, background):
    regions=_components((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==background)
    h,w=len(grid),len(grid[0])
    return [part for part in regions if all(0<r<h-1 and 0<c<w-1 for r,c in part)]


@lru_cache(maxsize=512)
def _analyze(frozen):
    counts=Counter(v for row in frozen for v in row)
    background=max(sorted(counts),key=counts.get)
    objects=_components(((r,c) for r,row in enumerate(frozen) for c,v in enumerate(row) if v!=background),True)
    palettes=[{frozen[r][c] for r,c in part} for part in objects]
    masks=[i for i,colors in enumerate(palettes) if len(colors)==1]
    tiles=[i for i,colors in enumerate(palettes) if len(colors)>1]
    if len(objects)!=2 or len(masks)!=1 or len(tiles)!=1:
        raise ValueError('expected one monochrome mask and one connected multicolor tile')
    def crop(part):
        r0=min(r for r,c in part);r1=max(r for r,c in part)
        c0=min(c for r,c in part);c1=max(c for r,c in part)
        return [list(row[c0:c1+1]) for row in frozen[r0:r1+1]]
    mask=crop(objects[masks[0]]);tile=crop(objects[tiles[0]])
    mask_color=next(iter(palettes[masks[0]]));mh,mw=len(mask),len(mask[0]);th,tw=len(tile),len(tile[0])
    if mh*th>30 or mw*tw>30:
        raise ValueError('scaled mosaic exceeds 30x30')
    mosaic=[[background if mask[r//th][c//tw]==background else tile[r%th][c%tw]
             for c in range(mw*tw)] for r in range(mh*th)]
    return {'background':background,'mask_color':mask_color,'mask':mask,'tile':tile,
            'output':mosaic,'enclosed':_enclosed(mosaic,background),
            'mask_holes':_enclosed(mask,background)}


def analyze(grid):
    return deepcopy(_analyze(_grid(grid)))


def predict(grid, policy='repeat'):
    if policy not in RIVALS+('largest_enclosed',):
        raise ValueError('undeclared prediction policy')
    info=_analyze(_grid(grid));out=deepcopy(info['output']);pockets=info['enclosed']
    if policy=='repeat' or not pockets:
        return out
    if policy=='all_enclosed':
        selected=[p for part in pockets for p in part]
    elif policy=='smallest_enclosed':
        selected=min(pockets,key=len)
    elif policy=='first_enclosed':
        selected=pockets[0]
    elif policy=='last_enclosed':
        selected=pockets[-1]
    elif policy=='tile_holes':
        size=sum(row.count(info['background']) for row in info['tile'])
        selected=[p for part in pockets if len(part)==size for p in part]
    elif policy in ('mask_area','mask_area_last'):
        holes=info['mask_holes']
        if policy=='mask_area_last':holes=list(reversed(holes))
        if not holes:return out
        r,c=max(holes,key=len)[0]
        target=(r*len(info['tile']),c*len(info['tile'][0]))
        selected=next((part for part in pockets if target in part),[])
    else:
        selected=max(pockets,key=len)
    for r,c in selected:out[r][c]=info['mask_color']
    return out


def _transform(grid, rotation, reflected):
    result=deepcopy(grid)
    if reflected:result=[row[::-1] for row in result]
    for _ in range(rotation):result=[list(row) for row in zip(*result[::-1])]
    return result


def _scene(seed,index):
    rng=random.Random(f'bf45cf4b:inputs:v1:{seed}:{index}')
    palette=list(range(10));rng.shuffle(palette)
    bg,ink,base,accent=palette[:4]
    tile_sizes=[(3,3),(4,4),(3,4),(4,3),(4,4),(3,3),(3,3),(4,4),(5,4),(5,5)]
    th,tw=tile_sizes[index]
    mh,mw=(8,8) if index==0 else ((6,6) if index>=8 else (6,7))
    mask=[[ink]*mw for _ in range(mh)]
    if index==0:
        # Equal macro areas, unequal merged micro-pockets. The winner is
        # strictly between the two distractors on BOTH axes before D4.
        holes=[(1,1),(1,2),(3,4),(4,4),(6,5),(6,6)]
    elif index==1:
        holes=[(1,1),(1,2),(1,3),(3,mw-2),(4,mw-2),(4,1)]
    else:
        horizontal=3 if index in (2,4,6) else (1 if index==7 else 2)
        vertical=1 if index in (3,6,8) else 2
        holes=[(1,c) for c in range(1,1+horizontal)]
        holes += [(r,mw-2) for r in range(3,3+vertical)]
    for r,c in holes:
        mask[r][c]=bg
    # Boundary defects are outside the two equal-area enclosed mask holes.
    # Their presence distinguishes enclosed background from arbitrary blanks.
    if rng.randrange(2):mask[0][0]=bg
    if rng.randrange(2):mask[mh-1][0]=bg
    tile=[[base]*tw for _ in range(th)]
    for r in range(1,th-1):
        for c in range(1,tw):tile[r][c]=bg
    tile[0][0]=accent;tile[th-1][tw-1]=accent
    h,w=[(16,20),(17,22),(18,23),(19,24),(20,25),
         (21,26),(22,24),(23,26),(24,28),(25,30)][index]
    grid=[[bg]*w for _ in range(h)]
    # Exchange the two object locations across inputs; size/color never assigns
    # their roles. Only monochrome versus multicolor does.
    if rng.randrange(2):
        placements=[(mask,2,2),(tile,h-th-2,w-tw-2)]
    else:
        placements=[(tile,2,2),(mask,h-mh-2,w-mw-2)]
    for pattern,r0,c0 in placements:
        for r,row in enumerate(pattern):
            for c,value in enumerate(row):grid[r0+r][c0+c]=value
    if index<2:
        orient=random.Random(f'bf45cf4b:lesson-orientation:v1:{seed}')
        rotation=(orient.randrange(4)+2*index)%4;reflected=bool(orient.randrange(2))
    else:
        rotation=rng.randrange(4);reflected=bool(rng.randrange(2))
    result=_transform(grid,rotation,reflected)
    info=analyze(result);sizes=[len(p) for p in info['enclosed']]
    if not sizes or sizes.count(max(sizes))!=1:
        raise ValueError('construction lacks a unique largest mosaic pocket')
    return result


@lru_cache(maxsize=128)
def _bank(seed):
    return tuple(_scene(seed,index) for index in range(10))


def generate(seed, settings, demos=3, queries=4):
    policy=_setting(settings)
    if type(seed) is not int or not 0<=seed<2**63:
        raise ValueError('seed must be an integer in 0..2**63-1')
    if type(demos) is not int or not 2<=demos<=6:
        raise ValueError('demos must be an integer in 2..6')
    if type(queries) is not int or not 1<=queries<=4:
        raise ValueError('queries must be an integer in 1..4')
    bank=_bank(seed);permutation=list(range(4))
    random.Random(f'bf45cf4b:presentation:v1:{seed}').shuffle(permutation)
    def pair(index):
        grid=deepcopy(bank[index]);return {'input':grid,'output':predict(grid,policy)}
    return {'train':[pair(i) for i in range(demos)],
            'test':[pair(6+i) for i in permutation[:queries]],
            'program_solution':program(settings),
            'private':{'seed':seed,'settings':deepcopy(settings),'query_permutation':permutation}}


def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):
        raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
