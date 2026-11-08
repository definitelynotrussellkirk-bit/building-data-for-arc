"""General glyph-path interpreter and setting-blind constructive sampler.

No original grids or labels are imported here. The glyph codebook is the four
symbols learned from the public parent, not a table of complete puzzles.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import random
from pathlib import Path

SETTINGS = ('column_major', 'row_major')
GLYPHS = {
    1: ((1,1,0), (1,0,1), (0,1,0)),
    2: ((2,0,2), (2,0,2), (2,2,2)),
    3: ((3,3,3), (0,3,0), (3,0,3)),
    6: ((6,0,6), (0,6,0), (0,6,0)),
}
STEPS = {1: (3, 1), 2: (2, -1), 3: (4, -1), 6: (2, 0)}


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def setting(value):
    if type(value) is not dict or set(value) != {'read_order'} or value['read_order'] not in SETTINGS:
        raise ValueError('settings must contain exactly read_order=column_major or row_major')
    return value['read_order']


def _rng(seed, *key):
    token = '|'.join(map(str, ('136b0064-v1', seed, *key))).encode()
    return random.Random(int.from_bytes(hashlib.sha256(token).digest(), 'big'))


def decode(grid):
    """Return (top,left,color) glyph records and the right-hand canvas."""
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
            type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError('expected a 1..30 rectangular grid')
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('grid colors must be exact integers in 0..9')
    walls = [c for c in range(w) if all(grid[r][c] == 4 for r in range(h))]
    if len(walls) != 1 or walls[0] in (0,w-1):
        raise ValueError('one interior all-yellow divider is required')
    wall = walls[0]
    canvas = [row[wall+1:] for row in grid]
    if sum(v == 5 for row in canvas for v in row) != 1 or any(v not in (0,5) for row in canvas for v in row):
        raise ValueError('canvas must contain exactly one gray start on black')
    cells = {(r,c) for r in range(h) for c in range(wall) if grid[r][c] != 0}
    glyphs = []
    while cells:
        first = min(cells)
        color = grid[first[0]][first[1]]
        if color not in GLYPHS:
            raise ValueError('unknown glyph color')
        cells.remove(first)
        stack, component = [first], [first]
        while stack:
            r,c = stack.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    p = (r+dr,c+dc)
                    if p in cells and grid[p[0]][p[1]] == color:
                        cells.remove(p); stack.append(p); component.append(p)
        r0,c0 = min(r for r,c in component), min(c for r,c in component)
        shape = {(r-r0,c-c0) for r,c in component}
        want = {(r,c) for r,row in enumerate(GLYPHS[color]) for c,v in enumerate(row) if v}
        if shape != want:
            raise ValueError('malformed 3x3 instruction glyph')
        glyphs.append((r0,c0,color))
    if not glyphs:
        raise ValueError('empty instruction panel')
    return sorted(glyphs), canvas


def ordered_codes(glyphs, order):
    if order not in SETTINGS:
        raise ValueError('unknown reading order')
    key = (lambda x:(x[1],x[0])) if order == 'column_major' else (lambda x:(x[0],x[1]))
    return [g[2] for g in sorted(glyphs,key=key)]


def draw(canvas, codes, *, reset=False, unit_down=False, swap_lengths=False,
         offset=False, strict=False):
    """Thread the endpoint; rivals clip safely instead of throwing off-canvas."""
    out = [list(row) for row in canvas]
    starts = [(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v==5]
    if len(starts) != 1:
        raise ValueError('one start required')
    r,c = starts[0]
    c0 = c
    for color in codes:
        length, direction = STEPS[color]
        if swap_lengths and color in (1,3):
            length = 7-length
        if color == 6 and unit_down:
            length = 1
        if reset:
            c = c0
        cells = ([(r+1+j,c) for j in range(length)] if direction == 0 else
                 [(r+1,c+direction*(j+int(offset))) for j in range(length)])
        if strict and any(not (0<=rr<len(out) and 0<=cc<len(out[0])) for rr,cc in cells):
            raise ValueError('correct trace leaves canvas')
        for rr,cc in cells:
            if 0<=rr<len(out) and 0<=cc<len(out[0]):
                out[rr][cc] = color
        r,c = cells[-1]
    return out


def solve(grid, order='column_major'):
    glyphs, canvas = decode(grid)
    return draw(canvas,ordered_codes(glyphs,order),strict=True)


def validate_path(grid, order):
    solve(grid,order)
    return True


def rival_names(order):
    if order not in SETTINGS:
        raise ValueError('unknown reading order')
    return ('other_order','reverse','snake','deduplicate','sorted_colors',
            'reset_cursor','unit_down','swap_lengths','offset_start')


def rival_solve(grid, order, name):
    glyphs, canvas = decode(grid)
    codes = ordered_codes(glyphs,order)
    if name == 'other_order':
        codes = ordered_codes(glyphs, SETTINGS[1-SETTINGS.index(order)])
    elif name == 'reverse': codes = codes[::-1]
    elif name == 'snake':
        axis = 1 if order == 'column_major' else 0
        other = 1-axis
        groups = sorted({g[axis] for g in glyphs})
        codes = [g[2] for i,v in enumerate(groups)
                 for g in sorted((g for g in glyphs if g[axis]==v),
                                 key=lambda g:g[other], reverse=bool(i%2))]
    elif name == 'deduplicate': codes = list(dict.fromkeys(codes))
    elif name == 'sorted_colors': codes = sorted(codes)
    elif name not in ('reset_cursor','unit_down','swap_lengths','offset_start'):
        raise ValueError('unknown rival')
    return draw(canvas,codes,reset=name=='reset_cursor',unit_down=name=='unit_down',
                swap_lengths=name=='swap_lengths',offset=name=='offset_start')


def _geometry(codes):
    c = 0
    low = high = 0
    for color in codes:
        length,direction = STEPS[color]
        c += (length-1)*direction
        low,high = min(low,c),max(high,c)
    return low,high, len(codes)+codes.count(6)


def _candidate(seed, role, index, attempt=0, *, stress=False):
    rng = _rng(seed,role,index,attempt)
    if stress:
        nr,nc,h,w=7,4,30,30
        codes = [1]*14 + [2]*7 + [3]*6 + [6]
    else:
        profiles=((3,2),(2,3),(4,2),(3,3))
        nr,nc=profiles[index%4]
        n=nr*nc
        codes=[1,2,3,6] + rng.choices([1,2,3,6],weights=[4,2,2,1],k=n-4)
        h=rng.randint(max(4*nr-1, n+codes.count(6)+1), min(29,max(4*nr+3,n+codes.count(6)+4)))
        w=rng.randint(4*nc+12,30)
    rng.shuffle(codes)
    matrix=[codes[r*nc:(r+1)*nc] for r in range(nr)]
    orders=([matrix[r][c] for c in range(nc) for r in range(nr)],codes)
    geometries=[_geometry(s) for s in orders]
    low=min(x[0] for x in geometries); high=max(x[1] for x in geometries)
    wall=4*nc-1; width=w-wall-1
    if high-low >= width:
        return None
    start_c=rng.randint(-low,width-1-high)
    start_r=0 if stress else rng.randint(0,h-1-geometries[0][2])
    top=0 if stress else rng.randint(0,h-(4*nr-1))
    grid=[[0]*w for _ in range(h)]
    for r in range(h): grid[r][wall]=4
    grid[start_r][wall+1+start_c]=5
    for r in range(nr):
        for c in range(nc):
            shape=GLYPHS[matrix[r][c]]
            for dr in range(3):
                for dc in range(3):
                    grid[top+4*r+dr][4*c+dc]=shape[dr][dc]
    return grid


def _make_input(seed, role, index, *, stress=False, teaching=False):
    for attempt in range(2048):
        grid=_candidate(seed,role,index,attempt,stress=stress)
        if grid is None: continue
        if teaching and any(rival_solve(grid,order,name)==solve(grid,order)
                            for order in SETTINGS for name in rival_names(order)):
            continue
        return grid
    raise ValueError('bounded sampler exhausted; no fallback lesson is emitted')


@lru_cache(maxsize=64)
def _bank(seed):
    train=[_make_input(seed,'train',i,teaching=i<2) for i in range(6)]
    test=[_make_input(seed,'query',i,stress=i==3) for i in range(4)]
    _rng(seed,'presentation').shuffle(test)
    inputs=train+test
    if len({str(g) for g in inputs}) != len(inputs):
        raise ValueError('duplicate inputs; refuse ambiguous episode')
    return train,test


@lru_cache(maxsize=128)
def full_lesson(seed, order):
    train,test=_bank(seed)
    return {split:tuple((tuple(tuple(r) for r in g),tuple(tuple(r) for r in solve(g,order)))
                       for g in grids) for split,grids in [('train',train),('test',test)]}


def sample_input(seed, sample_index, difficulty='medium'):
    integer(seed,0,2**63-1,'seed'); integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in ('easy','medium','hard'):
        raise ValueError('difficulty must be easy, medium or hard')
    return _make_input(seed,'production-'+difficulty,sample_index,
                       stress=difficulty=='hard',teaching=False)


def racket_program(order='column_major', rival=None):
    """Compile named, total finite rivals from one explicit Racket interpreter."""
    if order not in SETTINGS: raise ValueError('unknown reading order')
    if rival is not None and rival not in rival_names(order): raise ValueError('unknown rival')
    selected = SETTINGS[1-SETTINGS.index(order)] if rival=='other_order' else order
    primary,secondary=('obj-c1','obj-r1') if selected=='column_major' else ('obj-r1','obj-c1')
    comparator=f'(lambda (a b) (if (= ({primary} a) ({primary} b)) (< ({secondary} a) ({secondary} b)) (< ({primary} a) ({primary} b))))'
    codes='(map obj-color ordered)'
    if rival=='reverse': codes=f'(reverse {codes})'
    elif rival=='deduplicate': codes=f'(remove-duplicates {codes})'
    elif rival=='sorted_colors': codes=f'(sort {codes} <)'
    elif rival=='snake':
        codes=f'''(apply append
        (for/list ((v (sort (remove-duplicates (map {primary} glyphs)) <)) (i (in-naturals)))
          (map obj-color (sort (filter (lambda (o) (= ({primary} o) v)) glyphs)
            (lambda (a b) (if (even? i) (< ({secondary} a) ({secondary} b)) (> ({secondary} a) ({secondary} b))))))))'''
    return f'''(rule!
 ;; Decode colored 3x3 instructions on the left of the yellow divider.
 ;; Read {selected.replace('_',' ')}; 1=right3, 2=left2, 3=left4, 6=down2.
 ;; Start below the gray marker and thread the endpoint through every stroke.
 ;; Horizontal strokes include the entry column. The right canvas is the output.
 (lambda (g)
  (let ()
   (define wall (first (filter (lambda (c) (for/and ((r (range (rows g)))) (= (at g r c) 4))) (range (cols g)))))
   (define canvas (subgrid g 0 (+ wall 1) (- (rows g) 1) (- (cols g) 1)))
   (define glyphs (filter (lambda (o) (< (obj-c2 o) wall)) (objects-8 g 0)))
   (define ordered (sort glyphs {comparator}))
   (define codes {codes})
   (define start (first (find-color canvas 5)))
   (define result
    (for/fold ((state (list canvas (first start) (second start)))) ((color codes))
     (let* ((out (first state)) (r (second state)) (c {'(second start)' if rival=='reset_cursor' else '(third state)'})
            (n (cond ((= color 1) {4 if rival=='swap_lengths' else 3}) ((= color 2) 2) ((= color 3) {3 if rival=='swap_lengths' else 4}) (else {1 if rival=='unit_down' else 2})))
            (direction (cond ((= color 1) 1) ((= color 6) 0) (else -1)))
            (cells (for/list ((j (range n)))
                     (if (= direction 0) (list (+ r 1 j) c)
                       (list (+ r 1) (+ c (* direction (+ j {1 if rival=='offset_start' else 0})))))))
            (painted (for/fold ((a out)) ((p cells))
                       (if (in-bounds? (first p) (second p) (rows out) (cols out))
                         (set-cell a (first p) (second p) color) a)))
            (endpoint (last cells)))
       (list painted (first endpoint) (second endpoint)))))
   (first result))))
'''
