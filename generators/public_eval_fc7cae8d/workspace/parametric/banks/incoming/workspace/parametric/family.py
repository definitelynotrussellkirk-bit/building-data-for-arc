"""Frame-guided dihedral crop and post-orientation notch closure.

The two distinct colored frame edges identify the unique dihedral transform.
The outer gray/black border is noise. Labels have no dependency on parent golds.
"""
from collections import Counter, deque


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
        type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30 or
        any(type(row) is not list or len(row) != len(grid[0]) or
            any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError('Expected a rectangular 1..30 integer-color grid')
    return grid


def transform(grid, code):
    if type(code) is not int or code not in range(8):
        raise ValueError('Dihedral code must be an integer in 0..7')
    out = [row[:] for row in grid]
    if code >= 4:
        out = [row[::-1] for row in out]
    for _ in range(code % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def components(grid, predicate=lambda v: v != 0, diagonal=False):
    h, w = len(grid), len(grid[0])
    unseen = {(r,c) for r in range(h) for c in range(w) if predicate(grid[r][c])}
    delta = [(r,c) for r in (-1,0,1) for c in (-1,0,1)
             if (r or c) and (diagonal or abs(r)+abs(c)==1)]
    result = []
    while unseen:
        seed = min(unseen); unseen.remove(seed); cells = {seed}; stack = [seed]
        while stack:
            r,c = stack.pop()
            for dr,dc in delta:
                q = r+dr,c+dc
                if q in unseen:
                    unseen.remove(q); cells.add(q); stack.append(q)
        result.append(cells)
    return result


def sides(grid):
    return [grid[0], [row[-1] for row in grid], grid[-1], [row[0] for row in grid]]


def edge_for(grid, color):
    counts = [row.count(color) for row in sides(grid)]
    return max(range(4), key=lambda k: counts[k])


def decode(grid):
    validate_grid(grid)
    h,w = len(grid),len(grid[0]); guides = {}
    for side, row in enumerate(sides(grid)):
        count = Counter(v for v in row if v not in (0,5))
        if count:
            color, n = count.most_common(1)[0]
            if n * 2 > len(row):
                guides[color] = side
    if len(guides) != 2 or (next(iter(guides.values())) - list(guides.values())[1]) % 2 != 1:
        raise ValueError('Two adjacent, distinct colored outer frame edges required')
    inner = [s for s in components(grid, diagonal=True)
             if all(0 < r < h-1 and 0 < c < w-1 for r,c in s)]
    if not inner:
        raise ValueError('No isolated interior framed picture')
    cells = max(inner, key=len)
    r0,r1 = min(r for r,c in cells), max(r for r,c in cells)
    c0,c1 = min(c for r,c in cells), max(c for r,c in cells)
    frame = [row[c0:c1+1] for row in grid[r0:r1+1]]
    source = {color: edge_for(frame,color) for color in guides}
    if len(set(source.values())) != 2 or (list(source.values())[0]-list(source.values())[1]) % 2 != 1:
        raise ValueError('Interior frame must have two adjacent guide edges')
    matches = [k for k in range(8) if all(edge_for(transform(frame,k),color)==side for color,side in guides.items())]
    if len(matches)!=1:
        raise ValueError('Frame does not uniquely determine orientation')
    used = set(source.values())
    a,b = int(0 in used), len(frame)-int(2 in used)
    c,d = int(3 in used), len(frame[0])-int(1 in used)
    payload = [row[c:d] for row in frame[a:b]]
    return {'payload': payload, 'transform': matches[0], 'outer': guides, 'inner': source}


def seal_top(grid):
    """Fill exactly the 4-connected zero regions incident to the top edge."""
    out = [row[:] for row in grid]
    counts = Counter(v for row in grid for v in row if v != 0)
    fill = min(counts, key=lambda v: (-counts[v], v)) if counts else 0
    for cells in components(grid, lambda v: v == 0):
        if any(r == 0 for r,c in cells):
            for r,c in cells:
                out[r][c] = fill
    return out


def solve(grid, finish='orient'):
    if finish not in ('orient','seal_top'):
        raise ValueError('Undeclared finish')
    info = decode(grid)
    out = transform(info['payload'], info['transform'])
    return out if finish == 'orient' else seal_top(out)

# Scene sampling and public projection intentionally use distinct RNG streams.
import copy
import hashlib
import json
import random
from pathlib import Path
BASE = Path(__file__).resolve().parent
SETTINGS = ('orient', 'seal_top')


def rng(seed, stream):
    return random.Random(int.from_bytes(hashlib.sha256(f'{seed}/{stream}'.encode()).digest(), 'big'))


def scene(seed, index, n, code=None):
    prng = rng(seed, f'scene/{index}')
    guides = prng.sample([1,2,3,4,6,7,8,9],2)
    colors = [v for v in range(1,10) if v not in guides and v != 5]
    bg,accent,accent2 = prng.sample(colors,3)
    ph,pw = prng.randint(8,n-7),prng.randint(9,n-7)
    if n==30: ph,pw=22,23
    p = [[bg]*pw for _ in range(ph)]
    # Three different open-edge notches and one enclosed hole. The top opening
    # reaches an offset chamber, not merely the cells on the top border.
    for r in range(4): p[r][2]=0
    for r in (2,3):
        for c in range(2,5): p[r][c]=0
    for c in range(pw-3,pw): p[ph-3][c]=0
    for r in range(ph-2,ph): p[r][pw//2]=0
    p[ph//2][pw//2]=0
    # Asymmetric internal marks destroy all nonidentity dihedral symmetries.
    for r,c in [(ph//2,1),(ph//2+1,1),(ph//2+1,2)]: p[r][c]=accent
    for c in range(pw-5,pw-2): p[1][c]=accent2
    for r in range(5,ph-3,3):
        for c in range(3,pw-3,4):
            if p[r][c]: p[r][c]=prng.choice([bg,bg,accent,accent2])
    if code is None: code=prng.randrange(8)
    inverse=next(k for k in range(8) if transform(transform([[1,2,3],[4,5,6]],k),code)==[[1,2,3],[4,5,6]])
    src=transform(p,inverse)
    e0=prng.randrange(4); e1=(e0+1)%4; edge_colors={e0:guides[0],e1:guides[1]}
    sh,sw=len(src),len(src[0]); frame=[[0]*(sw+1) for _ in range(sh+1)]
    ro,co=int(0 in edge_colors),int(3 in edge_colors)
    for r in range(sh): frame[ro+r][co:co+sw]=src[r][:]
    for e,color in edge_colors.items():
        if e in (0,2):
            for c in range(co,co+sw): frame[0 if e==0 else sh][c]=color
        else:
            for r in range(ro,ro+sh): frame[r][sw if e==1 else 0]=color
    g=[[0]*n for _ in range(n)]
    r0=prng.randint(3,n-len(frame)-3); c0=prng.randint(3,n-len(frame[0])-3)
    for r,row in enumerate(frame): g[r0+r][c0:c0+len(row)]=row
    signature=[[0,0,0],[0,0,0],[0,0,0]]
    for e,color in edge_colors.items():
        rr,cc=[(0,1),(1,2),(2,1),(1,0)][e];signature[rr][cc]=color
    sig=transform(signature,code)
    target={edge_for(sig,color):color for color in guides}
    for e in range(4):
        for t in range(n):
            r,c=[(0,t),(t,n-1),(n-1,t),(t,0)][e]
            if e in target: g[r][c]=target[e]
            elif g[r][c]==0 and prng.random()<0.55: g[r][c]=5
        if e in target:
            for t in range(2,n-2):
                if prng.random()<0.25:
                    r,c=[(1,t),(t,n-2),(n-2,t),(t,1)][e];g[r][c]=target[e]
    return g


def check_settings(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or type(settings['finish']) is not str or settings['finish'] not in SETTINGS:
        raise ValueError('Exactly one declared finish setting is required')
    return settings['finish']


def program(settings):
    finish=check_settings(settings)
    return (BASE/('canonical.rkt' if finish=='orient' else 'seal_top.rkt')).read_text()


def generate(seed, settings, demos=2, queries=4):
    finish=check_settings(settings)
    if type(seed) is not int or seed<0 or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('Nonnegative integer seed, 2..6 demos and 1..4 queries required')
    demo_sizes=[18,22,20,26,24,28]
    codes=[1+seed%3,4+seed%4]+[rng(seed,f'code/{i}').randrange(8) for i in range(2,6)]
    train_in=[scene(seed,f'demo/{i}',demo_sizes[i],codes[i]) for i in range(demos)]
    bank=[scene(seed,f'query/{i}',n) for i,n in enumerate([30,24,27,29])]
    order=list(range(4));rng(seed,'presentation').shuffle(order)
    pair=lambda x: {'input':x, 'output':solve(x,finish)}
    return {'train':[pair(x) for x in train_in], 'test':[pair(bank[i]) for i in order[:queries]],
            'program_solution':program(settings),
            'private':{'source_indices':order[:queries], 'settings':copy.deepcopy(settings), 'seed':seed}}


def public_turn(episode, index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):
        raise ValueError('No such current query')
    return copy.deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']], 'test':[{'input':episode['test'][index]['input']}]})


def rival_names(finish):
    names=[f'fixed_{k}' for k in range(8)] + ['rotation_only']
    return names + (['other_setting','wrong_order','all_holes','top_row_only'] if finish=='seal_top' else ['other_setting'])


def rival(grid, finish, name):
    info=decode(grid); payload=info['payload']; k=info['transform']; out=transform(payload,k)
    if name.startswith('fixed_'): out=transform(payload,int(name[-1]))
    elif name=='rotation_only': out=transform(payload,k%4)
    elif name=='other_setting': return solve(grid,'seal_top' if finish=='orient' else 'orient')
    elif name=='wrong_order': return transform(seal_top(payload),k)
    elif name=='all_holes':
        bg=Counter(v for row in out for v in row if v).most_common(1)[0][0]
        return [[bg if v==0 else v for v in row] for row in out]
    elif name=='top_row_only':
        filled=seal_top(out); return [filled[0]]+[row[:] for row in out[1:]]
    else: raise ValueError(name)
    return seal_top(out) if finish=='seal_top' else out


def rival_program(finish,name):
    source=(BASE/'canonical.rkt').read_text()
    if name=='other_setting': return program({'finish':'seal_top' if finish=='orient' else 'orient'})
    if name.startswith('fixed_'): expression=f'(tx payload {int(name[-1])})'
    elif name=='rotation_only': expression='(tx payload (modulo code 4))'
    elif name=='wrong_order': expression='(tx (seal payload) code)'
    elif name=='all_holes': expression='(cellmap oriented (r c v) (if (= v 0) (mode oriented 0) v))'
    elif name=='top_row_only': expression='(cons (first (seal oriented)) (rest oriented))'
    else: raise ValueError(name)
    if (name.startswith('fixed_') or name=='rotation_only') and finish=='seal_top': expression=f'(seal {expression})'
    return source.replace(';; RESULT\n    oriented))',f';; RESULT\n    {expression}))')
