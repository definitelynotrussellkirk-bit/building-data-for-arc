"""Native exact-two composition. Python labels are claims rechecked by Racket.

Stage A freezes input counts while joining vertical exact-two groups. In the
alternate setting Stage B freezes that intermediate and joins horizontal
exact-two groups; newly completed bars may create OR suppress horizontal joins.
Inputs are sampled independently of the private composition setting.
"""
from __future__ import annotations

from pathlib import Path
from collections import Counter
import hashlib
import json
import random

HOME = Path(__file__).resolve().parent
MODES = ('vertical_only', 'vertical_then_horizontal')


def _mode(settings):
    if type(settings) is not dict or set(settings) != {'composition'} or settings['composition'] not in MODES:
        raise ValueError('settings require exactly composition=vertical_only|vertical_then_horizontal')
    return settings['composition']


def _grid(g):
    if type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list or not 1 <= len(g[0]) <= 30:
        raise ValueError('grid must have 1..30 rows and columns')
    w = len(g[0])
    if any(type(row) is not list or len(row) != w or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g):
        raise ValueError('grid must contain rectangular exact integer colors 0..9')


def _pass_rkt(axis, name):
    """Pass freezes x for both counts and color order; only out/acc are mutated."""
    line_count = '(cols x)' if axis == 'vertical' else '(rows x)'
    line = '(col x i)' if axis == 'vertical' else '(row x i)'
    length = '(rows x)' if axis == 'vertical' else '(cols x)'
    at = '(at x j i)' if axis == 'vertical' else '(at x i j)'
    cell = '(list j i)' if axis == 'vertical' else '(list i j)'
    return f'''({name} (lambda (x)
      (for/fold ((out x)) ((i (in-range {line_count})))
        (for/fold ((acc out)) ((color (in-list (remove-duplicates (filter (lambda (v) (not (= v 0))) {line})))))
          (let ((hits (filter (lambda (j) (= {at} color)) (range {length}))))
            (if (= (length hits) 2)
                (paint-cells acc (map (lambda (j) {cell}) (range (apply min hits) (+ (apply max hits) 1))) color)
                acc))))))'''


def composition_program(order='vh'):
    if order not in ('vh', 'hv', 'h', 'vhvh'):
        raise ValueError('unknown composition')
    expression = {'vh': '(hp (vp g))', 'hv': '(vp (hp g))', 'h': '(hp g)', 'vhvh': '(hp (vp (hp (vp g))))'}[order]
    return '(rule! (let (' + _pass_rkt('vertical', 'vp') + '\n' + _pass_rkt('horizontal', 'hp') + ')\n' + expression + '))'


def program(settings):
    mode = _mode(settings)
    return (HOME / 'canonical.rkt').read_bytes().decode('utf-8') if mode == MODES[0] else composition_program()


def pass_axis(g, axis, *, exact=True, preserve_nonzero=False):
    """Independent Python claim model, also supplies named finite ablations."""
    _grid(g)
    if axis not in ('vertical', 'horizontal'):
        raise ValueError('axis must be vertical or horizontal')
    out = [row[:] for row in g]
    h, w = len(g), len(g[0])
    for i in range(w if axis == 'vertical' else h):
        cells = [(j,i) if axis == 'vertical' else (i,j) for j in range(h if axis == 'vertical' else w)]
        colors = dict.fromkeys(g[r][c] for r,c in cells if g[r][c])
        for color in colors:
            hits = [j for j,(r,c) in enumerate(cells) if g[r][c] == color]
            if len(hits) == 2 or (not exact and len(hits) > 2):
                for r,c in cells[hits[0]:hits[-1]+1]:
                    if not preserve_nonzero or not g[r][c]:
                        out[r][c] = color
    return out


def solve(g, mode):
    if mode not in MODES:
        raise ValueError('unknown composition')
    v = pass_axis(g, 'vertical')
    return v if mode == MODES[0] else pass_axis(v, 'horizontal')


def _scene(seed, split, index):
    shapes = ((10,11),(12,13),(14,15),(16,17),(18,19),(20,21)) if split == 'train' else ((11,12),(17,18),(24,25),(30,30))
    h,w = shapes[index]
    digest = hashlib.sha256(f'exact2-composition-v1/{seed}/{split}/{index}'.encode()).digest()
    rng = random.Random(int.from_bytes(digest, 'big'))
    a,b,c,d,e,f = rng.sample(range(1,10),6)
    g = [[0]*w for _ in range(h)]
    # Full-span and offset bars of A; a shorter third bar suppresses the second
    # pass in its overlap interval. These differences are not just rectangles.
    columns = rng.sample(range(w),8)
    if split == 'train' and index == 0:
        # A wide horizontal input pair is destroyed by the vertical stage.
        # Reserve column 1 empty so doing horizontal first leaves a witness.
        columns = [3,6,9,2,4,8,0,w-1]
        # The third A bar blocks row filling; columns 5/7 cannot be painted
        # by another color, retaining the exact-two vs >=2 counterexample.
    if split == 'test' and index == 3:
        middle = rng.sample(range(1,w-1),6)
        columns = [0,w-1,*middle]
    x,y,z,u,v,t,m,n = columns
    def pair(col,color,top,bottom):
        g[top][col] = g[bottom][col] = color
    pair(x,a,0,h-3); pair(y,a,2,h-1)
    pair(z,a,h//2-1,h//2+1)
    # Two B bars with unequal extents, plus an unlike interior overwrite.
    pair(u,b,1,h-2); pair(v,b,3,h-1)
    g[h//2][u] = f
    # A true triple (never vertically filled) and unlike endpoints (never join).
    for r in (0,h//2,h-1): g[r][t] = c
    pair(m,d,0,h-1); g[h//2][m] = e
    g[h//2 if split == 'train' and index == 0 else 1][n] = e; g[h-2][n] = f
    # Larger cases carry actual extra columns, not an enlarged blank border.
    # Avoid A/B so their informative two/three-count windows remain present.
    if split == 'test' and index >= 2:
        for col in sorted(set(range(w))-set(columns)):
            color = rng.choice((c,d,e,f))
            top = rng.randrange(0,max(1,h//5))
            bottom = rng.randrange(h-h//5,h)
            pair(col,color,top,bottom)
            if (col+index)%4 == 0:
                g[rng.randrange(top+1,bottom)][col] = rng.choice([q for q in (c,d,e,f) if q != color])
    if split == 'train' and index == 1:
        # Two offset horizontal pairs with distinct endpoint columns. After
        # one VH cycle their overlap has exactly two cells per column, so a
        # second cycle would improperly fill the gap. No extra demonstration.
        g = [[0]*w for _ in range(h)]
        left = rng.randrange(0,2)
        right = w-1-rng.randrange(0,2)
        inner_left = w//2-2
        inner_right = w//2+1
        for rr,cc in ((1,left),(1,inner_right),(h-2,inner_left),(h-2,right)):
            g[rr][cc] = a
        g[2][w//2] = g[h-3][w//2] = b
        for rr in (0,h//2,h-1): g[rr][w-2] = c
        g[2][left] = d; g[h-3][left] = e
    if rng.randrange(2): g = list(reversed(g))
    if rng.randrange(2): g = [list(reversed(row)) for row in g]
    return g


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    if type(seed) is not int or seed < 0:
        raise ValueError('seed must be a nonnegative exact integer')
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError('demos must be an exact integer in 2..6')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('queries must be an exact integer in 1..4')
    result = {'program_solution':program(settings)}
    for split,count in (('train',demos),('test',queries)):
        grids = [_scene(seed,split,i) for i in range(count)]
        result[split] = [{'input':g,'output':solve(g,mode)} for g in grids]
    return result


def _bbox(g):
    out=[r[:] for r in g]
    for color in dict.fromkeys(v for row in g for v in row if v):
        cells=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==color]
        if len(cells)>1:
            for r in range(min(r for r,c in cells),max(r for r,c in cells)+1):
                for c in range(min(c for r,c in cells),max(c for r,c in cells)+1): out[r][c]=color
    return out


def _simultaneous(g):
    v=pass_axis(g,'vertical'); h=pass_axis(g,'horizontal')
    return [[h[r][c] if h[r][c]!=g[r][c] else v[r][c] for c in range(len(g[0]))] for r in range(len(g))]


def rivals():
    return {
      'vertical_only':lambda g:solve(g,MODES[0]),
      'vertical_then_horizontal':lambda g:solve(g,MODES[1]),
      'identity':lambda g:[r[:] for r in g],
      'horizontal_only':lambda g:pass_axis(g,'horizontal'),
      'horizontal_then_vertical':lambda g:pass_axis(pass_axis(g,'horizontal'),'vertical'),
      'simultaneous':_simultaneous,
      'vertical_at_least_two':lambda g:pass_axis(g,'vertical',exact=False),
      'both_at_least_two':lambda g:pass_axis(pass_axis(g,'vertical',exact=False),'horizontal',exact=False),
      'horizontal_at_least_two':lambda g:pass_axis(pass_axis(g,'vertical'),'horizontal',exact=False),
      'preserve_nonzero_vertical':lambda g:pass_axis(g,'vertical',preserve_nonzero=True),
      'preserve_nonzero_both':lambda g:pass_axis(pass_axis(g,'vertical',preserve_nonzero=True),'horizontal',preserve_nonzero=True),
      'color_bounding_boxes':_bbox,
      'repeat_vh_twice':lambda g:solve(solve(g,MODES[1]),MODES[1]),
    }


def teaching_audit(episode):
    # Fit only demonstrations. Query labels are used ONLY after the fit, to
    # report harmful survivors; an equivalent prediction is not a rejection.
    survivors=[]; failures=[]
    for name,fn in rivals().items():
        if all(fn(p['input'])==p['output'] for p in episode['train']):
            survivors.append(name)
            if any(fn(p['input'])!=p['output'] for p in episode['test']): failures.append(name)
    return {'policies_checked':len(rivals()),'survivors':survivors,'query_disagreeing_survivors':failures}


def public_turn_bytes(episode, query_index=0):
    from reviewer_support import public_challenge_bytes
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('query_index is out of range')
    return public_challenge_bytes({'train':episode['train'],'test':[episode['test'][query_index]]})
