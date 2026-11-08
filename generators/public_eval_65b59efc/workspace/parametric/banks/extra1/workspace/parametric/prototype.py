"""Table decoding and nested stencil assembly; Python labels are claims.

The reference Racket implementation is independently executed by authoring
preflight. This file never reads original tasks, gold labels or sibling homes.
"""
from __future__ import annotations
import hashlib
import random
from functools import lru_cache

MODES = ('as_drawn', 'clockwise')


def integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}')
    return value


def analyse(grid: list[list[int]]) -> dict:
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
        type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30 or
        any(type(row) is not list or len(row) != len(grid[0]) or
            any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError('expected a rectangular integer color grid of size 1..30')
    H, W = len(grid), len(grid[0])
    if 5 not in grid[0]:
        raise ValueError('missing gray table divider')
    n = grid[0].index(5)
    if not 2 <= n <= 5 or H < 2*n + 3:
        raise ValueError('template side must be 2..5 and include a legend')
    templates = []
    panels = []
    for x in range(0, W-n+1, n+1):
        colors = {grid[r][x+c] for r in range(n) for c in range(n)} - {0, 5}
        if not colors:
            continue
        if len(colors) != 1 or any(grid[r][x+c] == 5 for r in range(n) for c in range(n)):
            raise ValueError('each template slot must contain one non-gray source color')
        source = next(iter(colors))
        target_colors = {grid[r][x+c] for r in range(2*n+2, H) for c in range(n)} - {0, 5}
        if len(target_colors) != 1:
            raise ValueError('each active slot needs a single legend color')
        target = next(iter(target_colors))
        mask = [(r,c) for r in range(n) for c in range(n) if grid[r][x+c] == source]
        templates.append({'source': source, 'target': target, 'mask': mask, 'column': x})
        panels.append([[grid[n+1+r][x+c] for c in range(n)] for r in range(n)])
    sources = [t['source'] for t in templates]
    if not 2 <= len(sources) <= 8 or len(set(sources)) != len(sources):
        raise ValueError('expected distinct template source colors in at least two slots')
    layout = [[0]*n for _ in range(n)]
    for panel in panels:
        for r in range(n):
            for c in range(n):
                v = panel[r][c]
                if v and v not in sources:
                    raise ValueError('middle panel references an unknown template')
                if v and layout[r][c] not in (0, v):
                    raise ValueError('conflicting nonzero middle-panel overlap')
                if v:
                    layout[r][c] = v
    if not any(v for row in layout for v in row):
        raise ValueError('empty template layout')
    return {'n': n, 'templates': templates, 'layout': layout, 'panels': panels}


def transform(mask: list[tuple[int,int]], n: int, action: str) -> list[tuple[int,int]]:
    if action == 'as_drawn': return mask
    if action == 'clockwise': return [(c,n-1-r) for r,c in mask]
    if action == 'counterclockwise': return [(n-1-c,r) for r,c in mask]
    if action == 'half_turn': return [(n-1-r,n-1-c) for r,c in mask]
    if action == 'flip_lr': return [(r,n-1-c) for r,c in mask]
    if action == 'flip_ud': return [(n-1-r,c) for r,c in mask]
    if action == 'transpose': return [(c,r) for r,c in mask]
    if action == 'solid': return [(r,c) for r in range(n) for c in range(n)]
    raise ValueError('unknown template action')


def render(data: dict, action: str = 'as_drawn', foil: str | None = None) -> list[list[int]]:
    n, templates = data['n'], data['templates']
    by_source = {t['source']: (i,t) for i,t in enumerate(templates)}
    layout = data['layout']
    if foil == 'first_panel': layout = data['panels'][0]
    elif foil == 'last_panel': layout = data['panels'][-1]
    elif foil == 'transpose_layout': layout = [list(row) for row in zip(*layout)]
    elif foil == 'source_slot':
        layout = [[0]*n for _ in range(n)]
        for t,p in zip(templates, data['panels']):
            for r in range(n):
                for c in range(n):
                    if p[r][c]: layout[r][c] = t['source']
    if foil == 'layout_only': return [row[:] for row in layout]
    out = [[0]*(n*n) for _ in range(n*n)]
    for r in range(n):
        for c in range(n):
            v = layout[r][c]
            if not v: continue
            index,t = by_source[v]
            target = t['source'] if foil == 'source_colors' else t['target']
            mask = t['mask']
            if foil == 'reverse_templates': mask = templates[-1-index]['mask']
            if foil == 'reverse_legend': target = templates[-1-index]['target']
            for rr,cc in transform(mask,n,action):
                out[r*n+rr][c*n+cc] = target
    return out


def solve(grid: list[list[int]], mode: str = 'as_drawn') -> list[list[int]]:
    if mode not in MODES: raise ValueError('unknown tile orientation')
    return render(analyse(grid),mode)


@lru_cache(maxsize=2048)
def _policies(key: tuple) -> dict:
    data = analyse([list(r) for r in key])
    result = {a: render(data,a) for a in (*MODES,'counterclockwise','half_turn','flip_lr','flip_ud','transpose','solid')}
    for mode in MODES:
        for foil in ('first_panel','last_panel','source_slot','transpose_layout','source_colors','reverse_templates','reverse_legend'):
            result[mode+':'+foil] = render(data,mode,foil)
    result['layout_only'] = render(data,'as_drawn','layout_only')
    return result


def policy_outputs(grid: list[list[int]]) -> dict:
    return _policies(tuple(tuple(r) for r in grid))


def sample(seed: int, index: int, *, stress: bool = False) -> list[list[int]]:
    integer(seed,0,2**63-1,'seed'); integer(index,0,2**31-1,'index')
    rng = random.Random(int.from_bytes(hashlib.sha256(f'table-v1:{seed}:{index}'.encode()).digest(),'big'))
    n = 5 if stress else (3,5,4,2,5,3)[index%6]
    count = 5 if stress else rng.randint(2,min(5,30//(n+1),n*n-1))
    H = 30 if stress else 2*n+3+rng.randrange(1,4)
    W = 30 if stress else count*(n+1)-rng.randrange(2)
    grid = [[0]*W for _ in range(H)]
    sources = rng.sample([1,2,3,4,6,7,8,9],count)
    # Derange the recolors relative to the source table, avoiding numeric lookup.
    targets = sources[1:]+sources[:1]
    rng.shuffle(targets)
    if targets == sources: targets = targets[1:]+targets[:1]
    masks = []
    for i in range(count):
        for _ in range(512):
            mask = [(r,c) for r in range(n) for c in range(n) if rng.random() < .60]
            if len(mask) < 2 or len(mask) == n*n: continue
            if {r for r,c in mask} != set(range(n)) or {c for r,c in mask} != set(range(n)): continue
            if set(mask) == set(transform(mask,n,'clockwise')): continue
            if mask not in masks: break
        else: raise RuntimeError('bounded template sampling exhausted')
        masks.append(mask)
        x = i*(n+1)
        for r,c in mask: grid[r][x+c] = sources[i]
        if x+n < W:
            for r in range(H):
                if r%2 == 0 or stress: grid[r][x+n] = 5
        for r in (n,2*n+1):
            for c in range(x,min(x+n+1,W)):
                if (c-x)%2 == 0 or c==x+n: grid[r][c] = 5
        if stress:
            # Large single-color legend swatches are semantic data, not padding.
            for r in range(2*n+2,H):
                for c in range(n):
                    if r in (2*n+2,H-1) or c in (0,n-1) or rng.random()<.35:
                        grid[r][x+c] = targets[i]
        else:
            y = rng.randrange(2*n+2,H)
            for c in rng.sample(range(n),rng.randint(1,n)):
                grid[y][x+c] = targets[i]
    positions = [(r,c) for r in range(n) for c in range(n)]
    rng.shuffle(positions)
    active = positions[:rng.randint(max(count,n*n//2),n*n-1)]
    for k,(r,c) in enumerate(active):
        color = sources[k%count] if k<count else rng.choice(sources)
        # Panel position is independent of source identity (as in original data).
        panel = (sources.index(color)+1)%count if k<count else rng.randrange(count)
        grid[n+1+r][panel*(n+1)+c] = color
    analyse(grid)
    return grid
