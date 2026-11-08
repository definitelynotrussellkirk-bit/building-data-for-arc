"""Independent grid-level model for pointer-defined stencil transfer.

This module never reads official grids or labels. Racket remains label authority.
"""
from __future__ import annotations

DIRECTIONS = ((-1, 0), (0, -1), (0, 1), (1, 0))


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('Expected a rectangular 1..30 grid of exact integer colors')


def extract(grid):
    """Return source/target tails with input-derived, possibly hollow offsets.

    A tail is two distinct nonzero, non-cyan colors. Its ray must first hit
    cyan, not another color. Cyan is grouped by eight-connectivity. When two
    tails enter a touching component, eligible forward-facing cells go to the
    nearest tail axis (then nearest anchor and row-major tail on ties).
    """
    validate_grid(grid)
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8}
    components = []
    while remaining:
        start = min(remaining)
        todo = [start]; remaining.remove(start); cells = []
        while todo:
            r, c = todo.pop(); cells.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    q = (r+dr, c+dc)
                    if q in remaining:
                        remaining.remove(q); todo.append(q)
        components.append(sorted(cells))
    owner = {p: i for i, cells in enumerate(components) for p in cells}
    candidates = []
    for r in range(h):
        for c in range(w):
            source = grid[r][c]
            if source in (0, 8): continue
            for dr, dc in DIRECTIONS:
                tr, tc = r+dr, c+dc
                if not (0 <= tr < h and 0 <= tc < w): continue
                target = grid[tr][tc]
                if target in (0, 8, source): continue
                ar, ac = tr+dr, tc+dc
                rr, cc = ar, ac
                while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 0:
                    rr += dr; cc += dc
                if (rr, cc) not in owner: continue
                component = owner[rr, cc]
                candidates.append(dict(source=source, target=target, source_pos=(r,c),
                                       target_pos=(tr,tc), anchor=(ar,ac),
                                       direction=(dr,dc), component=component))
    assigned = [[] for _ in candidates]
    for i, cells in enumerate(components):
        tails = [(j, t) for j, t in enumerate(candidates) if t['component'] == i]
        for r, c in cells:
            eligible = [(j, t) for j,t in tails if
                        (r-t['anchor'][0])*t['direction'][0] +
                        (c-t['anchor'][1])*t['direction'][1] >= 0]
            if not eligible: continue
            def key(item):
                j,t = item; ar,ac=t['anchor']; dr,dc=t['direction']
                return (abs((r-ar)*dc-(c-ac)*dr), abs(r-ar)+abs(c-ac), j)
            j,t = min(eligible, key=key)
            assigned[j].append((r,c))
    rules = []
    for t, cells in zip(candidates, assigned):
        if not cells: continue
        ar, ac = t['anchor']
        rules.append(dict(t, cells=cells, offsets=[(r-ar,c-ac) for r,c in cells]))
    return rules


def apply(grid, rules, mode='as_drawn', *, only_first_seed=False,
          box=False, zero_anchor=False, keep_seeds=False, reverse_mapping=False):
    if mode not in ('as_drawn', 'quarter_turn'):
        raise ValueError('Unknown stencil action')
    h,w=len(grid),len(grid[0])
    tails = {p for t in rules for p in (t['source_pos'],t['target_pos'])}
    sources = {t['source'] for t in rules}
    out = [[v if v != 8 and (r,c) not in tails and (v not in sources or keep_seeds) else 0
            for c,v in enumerate(row)] for r,row in enumerate(grid)]
    for t in rules:
        offsets = t['offsets']
        if box:
            rs=[p[0] for p in offsets];cs=[p[1] for p in offsets]
            offsets=[(r,c) for r in range(min(rs),max(rs)+1) for c in range(min(cs),max(cs)+1)]
        if zero_anchor:
            mr=min(r for r,c in offsets);mc=min(c for r,c in offsets)
            offsets=[(r-mr,c-mc) for r,c in offsets]
        if mode == 'quarter_turn': offsets=[(c,-r) for r,c in offsets]
        source,target=t['source'],t['target']
        if reverse_mapping: source,target=target,source
        seeds=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row)
               if v==source and (r,c) not in tails]
        if only_first_seed: seeds=seeds[:1]
        for r,c in seeds:
            for dr,dc in offsets:
                rr,cc=r+dr,c+dc
                if 0<=rr<h and 0<=cc<w: out[rr][cc]=target
    return out


def solve(grid, mode='as_drawn'):
    return apply(grid, extract(grid), mode)
