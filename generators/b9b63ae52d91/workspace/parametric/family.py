"""Native mirror family. Python labels are claims; qualification executes Racket.

The input stream is independent of the chosen rule. A bounded, deterministic
set-cover lesson selector finds two witnesses for the declared finite rivals;
queries are generated separately, before teaching selection, never used as demos.
No claim of universal identifiability is made.
"""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
MODES = ('vertical', 'horizontal', 'paired_rows')
_spec = importlib.util.spec_from_file_location('b9_mirror_legacy_' + hashlib.sha256(str(HOME).encode()).hexdigest(), HOME / 'prototype.py')
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)

POLICIES = MODES + ('rotational', 'both_axes', 'either_axis', 'all_red', 'all_gray',
    'adjacent_vertical', 'any_same_column', 'opposite_half', 'axis_solo',
    'first_red_rows', 'last_red_rows', 'smallest_red_rows', 'largest_bbox_rows',
    'most_red_row', 'all_red_rows', 'cyan_component_rows', 'red8_component_rows',
    'largest_red_columns', 'tie_last_rows', 'relay_all_cyan_in_rows', 'relay_whole_rows')


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30):
        raise ValueError('grid must be a 1..30 rectangular list of exact 0/8 integers')
    w = len(grid[0])
    if any(type(row) is not list or len(row) != w or any(type(v) is not int or v not in (0,8) for v in row) for row in grid):
        raise ValueError('grid must be a 1..30 rectangular list of exact 0/8 integers')


def components(grid, color, diagonal=False):
    cells = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color}
    groups = []
    ds = [(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr or dc) and (diagonal or abs(dr)+abs(dc)==1)]
    while cells:
        start = min(cells); cells.remove(start)
        pending, group = [start], {start}
        while pending:
            r,c = pending.pop()
            for dr,dc in ds:
                p = (r+dr,c+dc)
                if p in cells:
                    cells.remove(p); group.add(p); pending.append(p)
        groups.append(sorted(group))
    return groups


def _largest(groups, last=False, bbox=False):
    if not groups:
        return []
    def size(g):
        return ((max(r for r,c in g)-min(r for r,c in g)+1) *
                (max(c for r,c in g)-min(c for r,c in g)+1)) if bbox else len(g)
    return min(groups, key=lambda g: (-size(g), tuple(-x for x in g[0]) if last else g[0]))


def intermediate(grid):
    validate_grid(grid)
    red = _legacy.apply_python(grid, 'vertical')
    winner = _largest(components(red,2))
    return {'size':len(winner), 'cells':[list(p) for p in winner], 'rows':sorted({r for r,c in winner})}


def solve(grid, policy):
    validate_grid(grid)
    if policy not in POLICIES:
        raise ValueError('unknown policy')
    if policy in ('vertical','horizontal'):
        return _legacy.apply_python(grid, policy)
    h,w = len(grid), len(grid[0])
    if policy in ('rotational','both_axes','either_axis','all_red','all_gray','adjacent_vertical','any_same_column','opposite_half','axis_solo'):
        out = [[0]*w for _ in range(h)]
        for r in range(h):
            for c in range(w):
                if grid[r][c] != 8: continue
                v = grid[h-1-r][c] == 8
                u = grid[r][w-1-c] == 8
                if policy == 'rotational': paired = grid[h-1-r][w-1-c] == 8
                elif policy == 'both_axes': paired = v and u
                elif policy == 'either_axis': paired = v or u
                elif policy == 'all_red': paired = True
                elif policy == 'all_gray': paired = False
                elif policy == 'adjacent_vertical': paired = any(0 <= rr < h and grid[rr][c]==8 for rr in (r-1,r+1))
                elif policy == 'any_same_column': paired = any(rr != r and grid[rr][c]==8 for rr in range(h))
                elif policy == 'opposite_half': paired = any((2*r-h+1)*(2*rr-h+1)<0 and grid[rr][c]==8 for rr in range(h))
                else: paired = v and r != h-1-r
                out[r][c] = 2 if paired else 5
        return out
    out = _legacy.apply_python(grid, 'vertical')
    groups = components(out,2)
    winner = _largest(groups)
    if policy == 'first_red_rows': winner = groups[0] if groups else []
    elif policy == 'last_red_rows': winner = groups[-1] if groups else []
    elif policy == 'smallest_red_rows': winner = min(groups,key=lambda g:(len(g),g[0])) if groups else []
    elif policy == 'largest_bbox_rows': winner = _largest(groups,bbox=True)
    elif policy == 'tie_last_rows': winner = _largest(groups,last=True)
    elif policy == 'cyan_component_rows': winner = _largest(components(grid,8))
    elif policy == 'red8_component_rows': winner = _largest(components(out,2,diagonal=True))
    selected = {r for r,c in winner}
    if policy == 'all_red_rows': selected = {r for g in groups for r,c in g}
    elif policy == 'most_red_row':
        selected = {max(range(h),key=lambda r:(out[r].count(2),-r))} if groups else set()
    columns = {c for r,c in winner}
    for r in range(h):
        for c in range(w):
            hit = c in columns if policy == 'largest_red_columns' else r in selected
            recolor = (out[r][c] == 5 or policy == 'relay_whole_rows' or
                       (policy == 'relay_all_cyan_in_rows' and out[r][c] == 2))
            if hit and recolor: out[r][c] = 4
    return out


def _scene(seed, role, index, h=None, w=None):
    """Independent hashed streams, plus constructive paired and solo edge anchors."""
    digest = hashlib.sha256(f'b9-native-v1:{seed}:{role}:{index}'.encode()).digest()
    rng = random.Random(int.from_bytes(digest,'big'))
    if h is None: h = (7,9,10,11,13,15)[index % 6]
    if w is None: w = (8,11,13,14,10,16)[(index//6) % 6]
    density = (0.38,0.47,0.56,0.66)[index % 4]
    g = [[8 if rng.random()<density else 0 for _ in range(w)] for _ in range(h)]
    # Non-axis pairs, a solo, self-mirror witnesses on odd heights, all four edges.
    g[0][0] = g[-1][0] = 8
    g[0][-1],g[-1][-1] = 8,0
    g[h//2][-1] = 8
    if h % 2: g[h//2][w//2] = 8
    return g


def _teaching_scene(seed):
    """A six-cell dense component defeats a five-cell, larger-box L.

    Gray payloads in both candidates' rows make selecting by bounding-box area
    visibly wrong. A diagonal singleton and an odd-axis singleton expose the
    connectivity and self-mirror branches without adding demonstrations.
    """
    rng = random.Random(int.from_bytes(hashlib.sha256(f'b9-construct:{seed}'.encode()).digest(),'big'))
    h,w = rng.choice((21,23,25)),rng.randrange(15,21)
    g = [[0]*w for _ in range(h)]
    rh,cw = rng.choice(((2,3),(3,2)))
    top,left = 1,rng.choice((1,2))
    red = {(r,c) for r in range(top,top+rh) for c in range(left,left+cw)}
    red.add((0,left-1))
    red |= {(6,8),(6,9),(6,10),(7,8),(8,8)}
    for r,c in red:
        g[r][c] = g[h-1-r][c] = 8
    g[h//2][w-2] = 8
    for r in (0,1,2,6,7): g[r][w-1] = 8
    if rng.randrange(2): g = [row[::-1] for row in g]
    return g


def _coverage(grid):
    outputs = {p:solve(grid,p) for p in POLICIES}
    return {(m,p) for m in MODES for p in POLICIES if outputs[m] != outputs[p]}


@lru_cache(maxsize=64)
def _bank(seed):
    queries = [_scene(seed,'query',i,*size) for i,size in enumerate(((9,12),(15,11),(22,25),(30,30)))]
    # Requirements are finite policies that can change one of the independent queries.
    need = set().union(*(_coverage(g) for g in queries))
    pool = [_scene(seed,'lesson',i) for i in range(48)]
    pool[0] = _teaching_scene(seed)
    masks = [_coverage(g) & need for g in pool]
    selected = None
    for i,j in itertools.combinations(range(len(pool)),2):
        if need <= masks[i] | masks[j]:
            selected = (i,j); break
    if selected is None:
        raise RuntimeError('No two-demo cover for declared finite rivals in bounded 48-scene pool')
    train = [pool[i] for i in selected]
    used = {json.dumps(g) for g in train + queries}
    for i in range(48):
        if len(train) == 6: break
        g = _scene(seed,'extra',i)
        key = json.dumps(g)
        if key not in used:
            used.add(key); train.append(g)
    if len(train) != 6 or len(used) != 10:
        raise RuntimeError('bounded distinct-input construction failed')
    return train,queries,{'pool_size':48,'selected_demo_indices':list(selected),'finite_obligations':len(need)}


def input_bank(seed):
    return copy.deepcopy(_bank(seed))


def teaching_check(episode):
    survivors = [p for p in POLICIES if all(solve(q['input'],p) == q['output'] for q in episode['train'])]
    bad = [p for p in survivors if any(solve(q['input'],p) != q['output'] for q in episode['test'])]
    return {'survivors':survivors, 'query_disagreeing_survivors':bad, 'scope':'declared finite Python policies; labels qualified separately'}


def public_view(episode, query_index):
    from reviewer_support import public_challenge_bytes
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('query_index must select one retained query')
    return json.loads(public_challenge_bytes({'train':episode['train'],'test':[episode['test'][query_index]]}))
