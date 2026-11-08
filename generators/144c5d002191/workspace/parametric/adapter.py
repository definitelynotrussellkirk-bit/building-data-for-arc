"""Native stamp policies. Claim labels are independently executed by qualification.

The legacy orientation materializer and component parser are reused by exact path.
Input draws never receive the hidden policy. No nested Racket work in generate().
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random

TASK = '144c5d002191'
HOME = Path(__file__).resolve().parent
POLICIES = ('identity','horizontal_mirror','visible_majority')
_spec = importlib.util.spec_from_file_location('_stamp_prior_' + TASK, HOME/'stamp_orientation.py')
prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prior)


def _settings(settings):
    if type(settings) is not dict or set(settings) != {'policy'}:
        raise ValueError('settings must contain exactly policy')
    value = settings['policy']
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f'policy must be one of {POLICIES}')
    return value


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in [{low}, {high}]')
    return value


def _majority_program(source):
    """Explicit numeric tie break, independent of unspecified mode-list ties."""
    canonical = (HOME/'canonical.rkt').read_text()
    return f'''(rule! (let* ((painted (let ((rule! (lambda (value) value))) {canonical}))
      (observed {source})
      (colors (filter (lambda (color) (not (= color 0))) (grid-colors observed)))
      (winner (if (null? colors) 0
        (first (sort colors (lambda (a b)
          (or (> (count-color observed a) (count-color observed b))
              (and (= (count-color observed a) (count-color observed b)) (< a b)))))))))
      (grid-from-fn (rows painted) (cols painted)
        (lambda (r c) (if (= (at painted r c) winner) winner 0)))))'''


def program(settings):
    policy = _settings(settings)
    if policy == 'identity':
        return (HOME/'canonical.rkt').read_text()
    if policy == 'horizontal_mirror':
        return prior.materialize_program('horizontal_mirror')
    return _majority_program('painted')


def counterfactual_program():
    # Count markers BEFORE clipping and overwrite. The template is excluded.
    source = '''(for/fold ((out (empty-grid (rows g) (cols g) 0)))
      ((obj (in-list (filter (lambda (x) (= (obj-size x) 1)) (objects g 0)))))
      (let ((p (first (obj-cells obj))))
        (set-cell out (first p) (second p) (obj-color obj))))'''
    return _majority_program(source)


def _parts(grid):
    parts = prior._components(grid)
    templates = [p for p in parts if len(p['cells']) > 1]
    if not templates:
        return None, []
    template = max(templates, key=lambda p: len(p['cells']))
    return template, [p for p in parts if len(p['cells']) == 1]


def input_errors(grid):
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        return ['expected nonempty list rows']
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ['ragged or empty grid']
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ['expected exact integer colors 0..9']
    if not 7 <= len(grid) <= 30 or not 7 <= len(grid[0]) <= 30:
        return ['sides outside 7..30']
    parts = prior._components(grid)
    if sum(len(p['cells']) > 1 for p in parts) != 1:
        return ['expected exactly one multi-cell monochromatic template']
    if not any(len(p['cells']) == 1 for p in parts):
        return ['missing singleton markers']
    return []


def _stamp(grid, *, mirror=False, order='row', edge='clip', box=False, occupied=False):
    h,w = len(grid), len(grid[0])
    out = [[0]*w for _ in range(h)]
    template, markers = _parts(grid)
    if template is None:
        return out
    r0,c0 = min(r for r,c in template['cells']),min(c for r,c in template['cells'])
    shape = sorted((r-r0,c-c0) for r,c in template['cells'])
    sh,sw = max(r for r,c in shape)+1,max(c for r,c in shape)+1
    if mirror:
        shape = [(r,sw-1-c) for r,c in shape]
    if box:
        shape = [(r,c) for r in range(sh) for c in range(sw)]
    if occupied:
        dr,dc=min(shape)
        shape=[(r-dr,c-dc) for r,c in shape]
    if order == 'reverse':
        markers=list(reversed(markers))
    elif order == 'color':
        markers=sorted(markers,key=lambda p:p['color'])
    elif order == 'color_desc':
        markers=sorted(markers,key=lambda p:-p['color'])
    elif order == 'column':
        markers=sorted(markers,key=lambda p:tuple(reversed(min(p['cells']))))
    for marker in markers:
        top,left=min(marker['cells'])
        targets=[(top+r,left+c) for r,c in shape]
        if edge == 'drop' and any(not(0<=r<h and 0<=c<w) for r,c in targets):
            continue
        for r,c in targets:
            if edge=='wrap':
                r,c=r%h,c%w
            if 0<=r<h and 0<=c<w and (order!='first_wins' or out[r][c]==0):
                out[r][c]=marker['color']
    return out


def winning_color(grid, *, least=False):
    counts=Counter(v for row in grid for v in row if v)
    return min(counts, key=lambda c: ((1 if least else -1)*counts[c],c)) if counts else 0


def _keep(grid,color):
    return [[v if v==color else 0 for v in row] for row in grid]


def predict(grid,policy):
    if policy not in POLICIES:
        raise ValueError('unknown policy')
    painted=_stamp(grid,mirror=policy=='horizontal_mirror')
    return _keep(painted,winning_color(painted)) if policy=='visible_majority' else painted


def _rng(seed,split,index):
    digest=hashlib.sha256(f'{TASK}:native-v1:{seed}:{split}:{index}'.encode()).digest()
    return random.Random(int.from_bytes(digest,'big'))


def _paint(grid,shape,top,left,color):
    for r,c in shape:
        grid[top+r][left+c]=color


def _lesson(rng,index):
    h,w=rng.randint(9,15),rng.randint(12,22)
    g=[[0]*w for _ in range(h)]
    colors=sorted(rng.sample(range(1,10),4))
    if index==0:
        shape=[(0,1),(0,2),(1,0),(1,1),(1,2),(1,3),(2,0)]
        _paint(g,shape,h-4,1,colors[0])
        high,low=colors[3],colors[1]
        anchors=[(0,w-4,high),(0,w-3,low),(0,w-2,high),(1,w-5,high)]
    else:
        shape=[(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1)]
        _paint(g,shape,h-5,1,colors[3])
        # Three raw-count winners are clipped; a single full stamp wins visibly.
        anchors=[(0,0,colors[1]),(h-2,w-7,colors[2])]
        anchors += [(h-1,w-1-k,colors[0]) for k in (0,2,4)]
    for r,c,v in anchors:
        g[r][c]=v
    return g


def _shape(rng,height,width):
    # Connected, varied polyomino; all choices are bounded, no rejection loop.
    cells={(0,0)}
    for _ in range(rng.randint(max(height,width),height*width)-1):
        frontier=sorted({(r+dr,c+dc) for r,c in cells
                         for dr,dc in ((1,0),(-1,0),(0,1),(0,-1))
                         if 0<=r+dr<height and 0<=c+dc<width}-cells)
        if not frontier:
            break
        cells.add(rng.choice(frontier))
    return sorted(cells)


def _random_scene(rng,h,w,stress=False):
    g=[[0]*w for _ in range(h)]
    colors=rng.sample(range(1,10),5)
    if stress:
        # Large connected comb plus many spatially spread markers. Both content
        # and resulting stamps exercise the whole 30x30 canvas, not empty padding.
        sh,sw=8,9
        shape=sorted({(r,0) for r in range(sh)} |
                     {(r,c) for r in (0,2,4,6,7) for c in range(sw)})
        top,left=10,10
        _paint(g,shape,top,left,colors[0])
        anchors=[(r,c) for r in (0,3,6,9,12,15,18,21,24,27,29)
                 for c in (0,4,8,21,25,29)]
        rng.shuffle(anchors)
        for k,(r,c) in enumerate(anchors):
            g[r][c]=colors[1+k%4]
    else:
        sh,sw=rng.randint(2,min(6,h-3)),rng.randint(2,min(6,w-3))
        shape=_shape(rng,sh,sw)
        top,left=rng.randrange(h-sh+1),rng.randrange(w-sw+1)
        _paint(g,shape,top,left,colors[0])
        available=[(r,c) for r in range(h) for c in range(w) if not g[r][c]]
        rng.shuffle(available)
        wanted=rng.randint(4,12)
        count=0
        for r,c in available:
            color=colors[1+count%4]
            if any(0<=y<h and 0<=x<w and g[y][x]==color
                   for y,x in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))):
                continue
            g[r][c]=color
            count+=1
            if count==wanted:
                break
        if count != wanted:
            raise RuntimeError('constructive placement exhausted')
    return g


def scene(seed,split,index):
    rng=_rng(seed,split,index)
    if split=='train' and index<2:
        g=_lesson(rng,index)
    else:
        if split=='test':
            h,w=((7,9),(16,20),(23,27),(30,30))[index]
        else:
            h,w=rng.randint(10,24),rng.randint(12,26)
        g=_random_scene(rng,h,w,stress=(split=='test' and index==3))
    errors=input_errors(g)
    if errors:
        raise RuntimeError(f'sampler violated grammar: {errors}')
    return g


def generate(seed,settings,demos,queries):
    policy=_settings(settings)
    _integer(seed,'seed',0,2**63-1)
    _integer(demos,'demos',2,6)
    _integer(queries,'queries',1,4)
    ep={'program_solution':program(settings),'settings':dict(settings)}
    for split,count in (('train',demos),('test',queries)):
        ep[split]=[]
        for i in range(count):
            g=scene(seed,split,i)
            ep[split].append({'input':g,'output':predict(g,policy)})
    return ep


def public_turn(episode,index):
    _integer(index,'query index',0,len(episode['test'])-1)
    return {'train':[{'input':deepcopy(p['input']), 'output':deepcopy(p['output'])}
                     for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}


def rival_predictions(grid,policy):
    """Finite, executable shortcut class. Errors are not counted as refutations."""
    results={f'setting:{p}':predict(grid,p) for p in POLICIES}
    painted=_stamp(grid,mirror=policy=='horizontal_mirror')
    finish=lambda out: _keep(out,winning_color(out)) if policy=='visible_majority' else out
    for order in ('reverse','first_wins','color','color_desc','column'):
        results['order:'+order]=finish(_stamp(grid,mirror=policy=='horizontal_mirror',order=order))
    for edge in ('drop','wrap'):
        results['edge:'+edge]=finish(_stamp(grid,mirror=policy=='horizontal_mirror',edge=edge))
    results['solid_bbox']=finish(_stamp(grid,mirror=policy=='horizontal_mirror',box=True))
    results['occupied_anchor']=finish(_stamp(grid,mirror=policy=='horizontal_mirror',occupied=True))
    results['identity_input']=deepcopy(grid)
    if policy=='visible_majority':
        _,markers=_parts(grid)
        counts=Counter(p['color'] for p in markers)
        results['raw_marker_majority']=_keep(painted,min(counts,key=lambda c:(-counts[c],c)))
        results['raw_input_majority']=_keep(painted,winning_color(grid))
        results['visible_minority']=_keep(painted,winning_color(painted,least=True))
        colors={v for row in painted for v in row if v}
        results['minimum_color']=_keep(painted,min(colors,default=0))
        results['maximum_color']=_keep(painted,max(colors,default=0))
    return results


def teaching_failures(episode):
    policy=episode['settings']['policy']
    train=[rival_predictions(p['input'],policy) for p in episode['train']]
    surviving=[name for name in train[0]
               if all(row[name]==pair['output'] for row,pair in zip(train,episode['train']))]
    failures=[]
    for name in surviving:
        for i,pair in enumerate(episode['test']):
            if rival_predictions(pair['input'],policy)[name]!=pair['output']:
                failures.append({'rival':name,'query_index':i})
    return failures
