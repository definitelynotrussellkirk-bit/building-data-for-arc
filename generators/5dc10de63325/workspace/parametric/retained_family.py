"""Native count/glyph family. Claims are re-executed by native qualification.

Legacy fill-order sources are reused by exact adjacent path. The new rule first
segments cyan components, then feeds the maximum component size to the existing
quarter-count glyph computation. No hidden setting affects the input RNG.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
from itertools import permutations
import json
from pathlib import Path
import random

TASK = '5dc10de63325'
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('cyan_legacy_' + hashlib.sha256(str(HERE).encode()).hexdigest()[:16], HERE/'prototype.py')
LEGACY = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LEGACY)
SETTINGS = (*LEGACY.ALLOWED_FILL_ORDERS, 'largest_component_count')
ORDER = LEGACY.FILL_ORDERS[LEGACY.DEFAULT_FILL_ORDER]


def _setting(settings):
    if type(settings) is not dict or set(settings) != {'fill_order'}:
        raise ValueError('settings must contain exactly fill_order')
    value = settings['fill_order']
    if type(value) is not str or value not in SETTINGS:
        raise ValueError('unsupported fill_order')
    return value


def program(settings):
    setting = _setting(settings)
    if setting != 'largest_component_count':
        return LEGACY.materialize_rule(setting)
    source = LEGACY.materialize_rule()
    old = '(count (length (find-color g 8)))'
    new = '''(count
                    (let ((cyan-objs (filter (lambda (obj) (= (obj-color obj) 8))
                                             (objects g 0))))
                      (if (null? cyan-objs) 0
                          (apply max (map (lambda (obj) (length (obj-cells obj)))
                                          cyan-objs)))))'''
    if source.count(old) != 1:
        raise ValueError('canonical count expression changed')
    return source.replace(old, new, 1)


def _grid(g):
    if type(g) is not list or not g or type(g[0]) is not list or not g[0]:
        raise ValueError('expected nonempty list grid')
    w = len(g[0])
    if any(type(row) is not list or len(row) != w or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g):
        raise ValueError('expected rectangular exact integer grid')
    return g


def cyan_components(g):
    _grid(g)
    pending = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == 8}
    result = []
    while pending:
        first = min(pending); pending.remove(first); todo = [first]; cells = []
        while todo:
            r,c = todo.pop(); cells.append((r,c))
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in pending:
                    pending.remove(q); todo.append(q)
        result.append(sorted(cells))
    return sorted(result, key=lambda cells: (-len(cells), cells[0]))


def cyan_sizes(g):
    return [len(c) for c in cyan_components(g)]


def _glyph(q, order):
    # The selected canonical source has explicit q=1..4 branches, not clamping.
    active = set(order[:q]) if 1 <= q <= 4 else set()
    return [[8 if r != 2 and c != 2 and (r if r < 2 else r-3, c if c < 2 else c-3) in active else 0
             for c in range(5)] for r in range(5)]


def predict(g, setting):
    _setting({'fill_order': setting}); _grid(g)
    count = (max(cyan_sizes(g), default=0) if setting == 'largest_component_count'
             else sum(v == 8 for row in g for v in row))
    order = LEGACY.FILL_ORDERS.get(setting, ORDER)
    return _glyph(count//4, order)


def _rng(seed, key):
    raw = hashlib.sha256(f'{TASK}:native-v1:{seed}:{key}'.encode()).digest()
    return random.Random(int.from_bytes(raw, 'big'))


def _polyomino(rng, n):
    # A 4x4 construction guarantees size-13 has bbox area 16, refuting a
    # bounding-box-area surrogate for the actual component's cell count.
    cells = {(0,0)}
    while len(cells) < n:
        frontier = sorted({q for r,c in cells for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))
                           if 0 <= q[0] < 4 and 0 <= q[1] < 4 and q not in cells})
        cells.add(rng.choice(frontier))
    return sorted(cells)


def _scene(seed, role, index):
    rng = _rng(seed, f'{role}:{index}')
    if role == 'train':
        sizes = ((5,1,1),(9,1,1),(13,1,1),(7,6,6),(10,3,1),(4,1,1))[index]
        h,w = 10 + 2*index, 11 + 2*index
    else:
        sizes = ((4,),(6,3,1),(10,3,1),(13,3,3))[index]
        h,w = ((11,12),(15,16),(21,24),(30,30))[index]
    g = [[0]*w for _ in range(h)]
    corners = [(False,False),(False,True),(True,False),(True,True)]; rng.shuffle(corners)
    for n,(bottom,right) in zip(sizes,corners):
        for r,c in _polyomino(rng,n):
            g[h-1-r if bottom else r][w-1-c if right else c] = 8
    # Noncyan colors are ignored by BOTH lawful programs. This opt-in native
    # extension preserves count semantics while supplying spatial distractors.
    palette = rng.sample([1,2,3,4,5,6,7,9], 3)
    density = .28 if (h,w)==(30,30) else (.12 if index%2 else .18)
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 and rng.random() < density:
                g[r][c] = rng.choice(palette)
    # Exact dense-stress lower bound, without adding extra cyan signal.
    if (h,w)==(30,30):
        nonzero = sum(v!=0 for row in g for v in row)
        for r,c in rng.sample([(r,c) for r in range(h) for c in range(w) if g[r][c]==0], max(0,200-nonzero)):
            g[r][c] = rng.choice(palette)
    return g


def generate(seed, settings, demos=4, queries=4):
    setting = _setting(settings)
    for name,value,low,high in (('seed',seed,0,None),('demos',demos,4,6),('queries',queries,1,4)):
        if type(value) is not int or value < low or (high is not None and value > high):
            raise ValueError(f'{name} outside native exact-integer limits')
    train = [_scene(seed,'train',i) for i in range(demos)]
    bank = [_scene(seed,'test',i) for i in range(4)]
    grids = train+bank
    if len({json.dumps(g) for g in grids}) != len(grids):
        raise ValueError('constructed duplicate grid')
    def pair(g): return {'input':g, 'output':predict(g,setting)}
    return {'train':[pair(g) for g in train], 'test':[pair(g) for g in bank[:queries]],
            'program_solution':program(settings), 'settings':dict(settings)}


def public_turn(episode, index):
    from reviewer_support import public_challenge_bytes
    if type(index) is not int or not 0 <= index < len(episode['test']):
        raise ValueError('invalid query index')
    return json.loads(public_challenge_bytes({'train':episode['train'], 'test':[episode['test'][index]]}))


def teaching(episode):
    """Finite analytical screen; no query answer participates in filtering."""
    grids=[p['input'] for split in ('train','test') for p in episode[split]]
    metrics=[]
    for g in grids:
        cc=cyan_components(g); sizes=[len(c) for c in cc]
        first=cc[0] if cc else [(0,0)]
        area=(max(p[0] for p in first)-min(p[0] for p in first)+1)*(max(p[1] for p in first)-min(p[1] for p in first)+1)
        metrics.append({'global':sum(sizes),'largest':max(sizes,default=0),
                        'second':sizes[1] if len(sizes)>1 else 0,'components':len(cc),
                        'nonzero':sum(v!=0 for row in g for v in row),'largest_bbox':area})
    candidates=[]
    for order in permutations(ORDER):
        for source in metrics[0]:
            for rounding in ('floor','ceiling','nearest','two_glyph'):
                outputs=[]
                for m in metrics:
                    n=m[source]
                    q=n//4 if rounding=='floor' else (n+3)//4 if rounding=='ceiling' else (n+2)//4 if rounding=='nearest' else 4 if n>=16 else 3
                    outputs.append(_glyph(q,order))
                candidates.append((f'{order}:{source}:{rounding}',outputs))
    for q in range(5): candidates.append((f'constant:{q}',[_glyph(q,ORDER)]*len(grids)))
    n=len(episode['train']); survivors=[]; disagreements=[]
    for name,outs in candidates:
        if all(outs[i]==p['output'] for i,p in enumerate(episode['train'])):
            survivors.append(name)
            bad=[j for j,p in enumerate(episode['test']) if outs[n+j]!=p['output']]
            if bad: disagreements.append({'policy':name,'queries':bad})
    return {'policies':len(candidates),'survivors':survivors,'query_disagreements':disagreements,
            'passed':bool(survivors) and not disagreements}
