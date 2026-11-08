"""Native D4 transform-transfer family, with exact canonical default source.

All input shapes are newly constructed connected polyominoes. Prototype areas
and ordered bounding boxes agree, but their D4 orbits differ. The inference
intermediate is a uniquely recoverable prototype-to-query transformation.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

from puzzle_generators.rule_wrap import wrap_rule

HOME = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    '_transfer_pose_base_' + hashlib.sha256(str(HOME).encode()).hexdigest()[:12],
    HOME.parents[1] / 'generator.py')
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
CANONICAL = (HOME/'canonical.rkt').read_text(encoding='utf-8')
SETTINGS = ('label_query','transfer_pose')
RIVALS = ('label_query','identity_other','inverse_pose','fixed_clockwise',
          'fixed_mirror','matched_color','recolor_query','first_prototype')
LABELS = (2,3,4,6,7,8,9)


def _policy(settings: dict) -> str:
    if (type(settings) is not dict or set(settings) != {'response_policy'}
            or type(settings['response_policy']) is not str
            or settings['response_policy'] not in SETTINGS):
        raise ValueError('settings must contain exactly response_policy=label_query|transfer_pose')
    return settings['response_policy']


def _parse(grid):
    info = _base.analyze_grid(grid)
    if info['errors']:
        raise ValueError('; '.join(info['errors']))
    if len(info['transform_candidates']) != 1:
        raise ValueError('the admitted family requires a unique D4 mapping')
    return info


def transform(grid: list[list[int]], policy: str) -> list[list[int]]:
    """Python claim interpreter; protected Racket remains the label authority."""
    if policy not in set(SETTINGS) | set(RIVALS):
        raise ValueError('unknown response policy')
    info = _parse(grid)
    if policy == 'label_query':
        return deepcopy(info['expected_output'])
    winner = info['match_side']
    other = 0 if policy == 'first_prototype' else 1-winner
    code = info['transform_candidates'][0]
    if policy == 'identity_other': code = 0
    elif policy == 'inverse_pose': code = {1:3,3:1}.get(code,code)
    elif policy == 'fixed_clockwise': code = 1
    elif policy == 'fixed_mirror': code = 4
    color = info['labels'][winner if policy == 'matched_color' else other]
    query = info['shapes'][2]
    top = min(r for r,c in query)
    left = min(c for r,c in query)
    cells = (query if policy == 'recolor_query' else
             [(r+top,c+left) for r,c in _base._orient(info['normalized_shapes'][other],code)])
    out = [[0]*info['panel_w'] for _ in range(info['grid_h'])]
    for r,c in cells:
        # Wrong fixed-pose rivals can be too wide; match Racket's explicit
        # clipping rather than accepting a runtime error as their rejection.
        if 0 <= r < len(out) and 0 <= c < len(out[0]): out[r][c] = color
    return out


@lru_cache(maxsize=None)
def rule_for(policy: str) -> str:
    if policy not in set(SETTINGS) | set(RIVALS):
        raise ValueError('unknown response policy')
    if policy == 'label_query': return CANONICAL
    code_expr = {'identity_other':'0','inverse_pose':'(cond ((= actual 1) 3) ((= actual 3) 1) (else actual))',
                 'fixed_clockwise':'1','fixed_mirror':'4'}.get(policy,'actual')
    other_expr = '0' if policy == 'first_prototype' else '(- 1 winner)'
    color_expr = 'matched-label' if policy == 'matched_color' else '(cell-at g 0 (* other (+ pw 1)))'
    cells_expr = 'qcells' if policy == 'recolor_query' else '''(map (lambda (p)
                    (list (+ top (first p)) (+ left (second p))))
                  (orient (panel-cells other) chosen-code))'''
    return f'''(rule! (lambda (g)
      ;; A: canonical D4 matching supplies the selected label and query cells.
      ;; Infer its unique prototype-to-query map; B transfers it to the other shape.
      (let ()
        (define stage ({wrap_rule(CANONICAL)} g))
        (define pw (cols stage))
        (define (cell< a b)
          (or (< (first a) (first b))
              (and (= (first a) (first b)) (< (second a) (second b)))))
        (define (norm cells)
          (if (null? cells) cells
            (let ((r0 (apply min (map first cells))) (c0 (apply min (map second cells))))
              (sort (map (lambda (p) (list (- (first p) r0) (- (second p) c0))) cells) cell<))))
        (define (orient cells code)
          (norm (map (lambda (p)
            (let ((r (first p)) (c (second p)))
              (cond ((= code 0) (list r c)) ((= code 1) (list c (- r)))
                    ((= code 2) (list (- r) (- c))) ((= code 3) (list (- c) r))
                    ((= code 4) (list r (- c))) ((= code 5) (list (- r) c))
                    ((= code 6) (list c r)) (else (list (- c) (- r)))))) cells)))
        (define (panel-cells k)
          (for*/list ((r (range (rows g))) (c (range pw))
                       #:when (= (cell-at g r (+ (* k (+ pw 1)) c)) 1)) (list r c)))
        (define qcells (filter (lambda (p) (not (= (cell-at stage (first p) (second p)) 0))) (grid-positions stage)))
        (define matched-label (if (null? qcells) 0 (cell-at stage (first (first qcells)) (second (first qcells)))))
        (define winner (if (= matched-label (cell-at g 0 0)) 0 1))
        (define qnorm (norm qcells))
        (define codes (filter (lambda (code) (equal? (orient (panel-cells winner) code) qnorm)) (range 8)))
        (define actual (if (null? codes) 0 (first codes)))
        (define chosen-code {code_expr})
        (define other {other_expr})
        (define top (if (null? qcells) 0 (apply min (map first qcells))))
        (define left (if (null? qcells) 0 (apply min (map second qcells))))
        (recolor-cells (empty-grid (rows stage) pw 0) {cells_expr} {color_expr}))))'''


def program(settings: dict) -> str:
    return rule_for(_policy(settings))


def _rng(seed: int, label: str) -> random.Random:
    raw = hashlib.sha256(f'transfer-pose-v1:{seed}:{label}'.encode()).digest()
    return random.Random(int.from_bytes(raw,'big'))


def _shape(rng, height, width, size):
    """Connected growth around a random full-span cross, not a stored bitmap."""
    for _ in range(256):
        row,col = rng.randrange(height),rng.randrange(width)
        cells = {(r,col) for r in range(height)} | {(row,c) for c in range(width)}
        while len(cells) < size:
            frontier = {(r+dr,c+dc) for r,c in cells for dr,dc in _base._CARDINAL
                        if 0 <= r+dr < height and 0 <= c+dc < width} - cells
            cells.add(rng.choice(sorted(frontier)))
        normalized = _base._normalize(cells)
        if len(_base._d4_variants(normalized)) == 8:
            return normalized
    raise RuntimeError('bounded asymmetric connected-shape construction exhausted')


def _scene(rng, height, panel_w, shape_h, shape_w, size, side, code):
    reference = _shape(rng,shape_h,shape_w,size)
    variants = _base._d4_variants(reference)
    for _ in range(256):
        other = _shape(rng,shape_h,shape_w,size)
        if other not in variants: break
    else: raise RuntimeError('bounded equal-statistic decoy construction exhausted')
    query = _base._orient(reference,code)
    shapes = (reference,other,query) if side == 0 else (other,reference,query)
    grid = [[0]*(3*panel_w+2) for _ in range(height)]
    for row in grid: row[panel_w] = row[2*panel_w+1] = 5
    labels = rng.sample(LABELS,2)
    grid[0][0],grid[0][panel_w+1] = labels
    for k,shape in enumerate(shapes):
        rh,cw = _base._bbox_shape(shape)
        if rh >= height or cw > panel_w:
            raise ValueError('shape does not fit its panel under the requested pose')
        top,left = rng.randint(1,height-rh),rng.randint(0,panel_w-cw)
        for r,c in shape: grid[top+r][k*(panel_w+1)+left+c] = 1
    info = _parse(grid)
    assert info['match_side'] == side and info['transform_candidates'] == (code,)
    return grid


@lru_cache(maxsize=64)
def _inputs(seed: int) -> tuple:
    teaching = _rng(seed,'teaching')
    side = teaching.randrange(2)
    # Fixed roles, fresh shapes: one invertible quarter-turn and one reflection
    # are sufficient to reject the finite fixed/inverse/positional alternatives.
    codes = (teaching.choice((1,3)),teaching.choice((4,5,6,7)))
    demos = []
    for slot in range(6):
        rng = _rng(seed,f'demo-{slot}')
        shape_h,shape_w = ((3,4),(4,4),(3,3),(4,5),(5,4),(5,5))[slot]
        area = ((shape_h+shape_w-1) + shape_h*shape_w)//2
        demos.append(_scene(rng, max(shape_h,shape_w)+rng.randint(3,5),
                            max(shape_h,shape_w)+rng.randint(1,3),shape_h,shape_w,
                            area,(side+slot)%2,codes[slot] if slot<2 else (seed+slot)%8))
    queries = []
    specs = ((5,4,3,3,6),(10,6,4,5,13),(15,9,6,8,31),(30,9,27,9,145))
    for slot,spec in enumerate(specs):
        rng = _rng(seed,f'query-{slot}')
        code = (0,2,4,5)[seed%4] if slot == 3 else (seed+slot*2)%8
        queries.append(_scene(rng,*spec,rng.randrange(2),code))
    if len({tuple(map(tuple,g)) for g in demos+queries}) != 10:
        raise RuntimeError('scene streams produced a duplicate input')
    for name in RIVALS:
        if all(transform(g,name) == transform(g,'transfer_pose') for g in demos[:2]):
            raise RuntimeError('two-demo teaching contract failed for '+name)
    return tuple(tuple(tuple(row) for row in g) for g in demos),tuple(tuple(tuple(row) for row in g) for g in queries)


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    policy = _policy(settings)
    if type(seed) is not int: raise ValueError('seed must be an exact integer')
    if type(demos) is not int or not 2 <= demos <= 6: raise ValueError('demos must be an exact integer in 2..6')
    if type(queries) is not int or not 1 <= queries <= 4: raise ValueError('queries must be an exact integer in 1..4')
    train,test = _inputs(seed)
    def pair(raw):
        grid = [list(row) for row in raw]
        return {'input':grid,'output':transform(grid,policy)}
    return {'train':[pair(g) for g in train[:demos]],'test':[pair(g) for g in test[:queries]],
            'program_solution':program(settings)}


def public_turn(episode: dict, query_index: int) -> dict:
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('query_index must identify one stored query')
    return {'train':deepcopy([{'input':p['input'],'output':p['output']} for p in episode['train']]),
            'test':[{'input':deepcopy(episode['test'][query_index]['input'])}]}


def describe(grid: list[list[int]]) -> dict:
    info = _parse(grid)
    h,w = len(grid),len(grid[0])
    return {'shape':[h,w],'match_side':info['match_side'],
            'transform_code':info['transform_candidates'][0],
            'unique_orientation':len(info['transform_candidates']) == 1,
            'prototype_sizes':[len(cells) for cells in info['shapes'][:2]],
            'prototype_boxes':[list(_base._bbox_shape(s)) for s in info['normalized_shapes'][:2]],
            'query_size':len(info['shapes'][2]),
            'query_bbox_span':list(_base._bbox_shape(info['normalized_shapes'][2])),
            'shape_quadrants':[sum((r>=h//2)*2+(c>=w//2)==q for r,row in enumerate(grid)
                                   for c,v in enumerate(row) if v==1) for q in range(4)]}
