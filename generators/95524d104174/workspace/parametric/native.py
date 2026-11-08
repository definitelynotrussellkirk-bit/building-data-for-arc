"""Cross-frame native family. Python labels are claims; qualification uses Racket.

The relay recomputes components AFTER the frame splits the original lines.
This module does not modify the selected canonical generator or rule.
"""
from __future__ import annotations
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
MODES = ('frame_4', 'frame_2', 'frame_8', 'largest_fragment')
PALETTE = (1, 2, 3, 5, 6, 7, 9)  # 4 is the cutter; 8 is the relay highlight.


def _load_legacy():
    spec = importlib.util.spec_from_file_location('_cross_frame_legacy_' + str(HOME), HOME/'prototype.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LEGACY = _load_legacy()


def settings_mode(settings):
    if type(settings) is not dict or set(settings) != {'rule'}:
        raise ValueError('settings must name exactly rule')
    mode = settings['rule']
    if type(mode) is not str or mode not in MODES:
        raise ValueError('undeclared rule setting')
    return mode


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def cross(h, w, r, c, vertical, horizontal, winner):
    g = [[0]*w for _ in range(h)]
    for y in range(h):
        g[y][c] = vertical
    g[r] = [horizontal]*w
    g[r][c] = (vertical, horizontal)[winner]
    return g


def facts(g):
    if (type(g) is not list or not 4 <= len(g) <= 30 or type(g[0]) is not list
            or not 4 <= len(g[0]) <= 30):
        raise ValueError('native cross dimensions must be 4..30')
    h, w = len(g), len(g[0])
    if any(type(row) is not list or len(row) != w or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g):
        raise ValueError('expected rectangular integer color grid')
    rows = [r for r in range(h) if all(g[r])]
    cols = [c for c in range(w) if all(g[r][c] for r in range(h))]
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError('one full crossing row and column required')
    r, c = rows[0], cols[0]
    if not 0 < r < h-1 or not 0 < c < w-1:
        raise ValueError('cross must be interior')
    v, z = g[0][c], g[r][0]
    if v == z or v not in PALETTE or z not in PALETTE or g[r][c] not in (v,z):
        raise ValueError('distinct allowed line colors required; 4/8 reserved')
    for y in range(h):
        for x in range(w):
            if (y,x) != (r,c) and g[y][x] != (v if x == c else z if y == r else 0):
                raise ValueError('clean constant-color cross required')
    return r,c,v,z


def frame(g, color=4, support='all'):
    r,c,_,_ = facts(g)
    out = deepcopy(g)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if (dy or dx) and (support == 'all' or
                 support == 'diagonals' and dy and dx or
                 support == 'arms' and (dy == 0 or dx == 0)):
                out[r+dy][c+dx] = color
    return out


def components(g):
    """Independent row-major 4-connected monochromatic flood, excluding 0/4."""
    h,w = len(g),len(g[0])
    visited, answer = set(), []
    for r in range(h):
        for c in range(w):
            if (r,c) in visited or g[r][c] in (0,4):
                continue
            pending, cells, value = [(r,c)], [], g[r][c]
            visited.add((r,c))
            while pending:
                y,x = pending.pop()
                cells.append([y,x])
                for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if (0 <= yy < h and 0 <= xx < w and (yy,xx) not in visited
                            and g[yy][xx] == value):
                        visited.add((yy,xx)); pending.append((yy,xx))
            answer.append(sorted(cells))
    return sorted(answer, key=lambda cells: (-len(cells), cells[0]))


def fragment_facts(g):
    after = frame(g)
    obj = components(after)[0]
    return {'size':len(obj), 'color':after[obj[0][0]][obj[0][1]], 'cells':obj}


def predict(g, mode):
    if mode.startswith('frame_'):
        return frame(g,int(mode[-1]))
    if mode == 'identity':
        facts(g); return deepcopy(g)
    if mode in ('diagonals','arms'):
        return frame(g, support=mode)
    after = frame(g)
    objects = components(after)
    r,c,v,z = facts(g)
    if mode == 'modal_center':
        counts = {x:sum(row.count(x) for row in g) for x in (v,z)}
        after[r][c] = max(counts, key=counts.get)
        return after
    chosen = objects[0]
    if mode == 'pre_ring':
        chosen = components(g)[0]
    elif mode == 'smallest_fragment':
        chosen = min(objects,key=lambda o:(len(o),o[0]))
    elif mode == 'second_fragment':
        chosen = objects[min(1,len(objects)-1)]
    elif mode == 'column_major_tie':
        chosen = min(objects,key=lambda o:(-len(o),o[0][1],o[0][0]))
    elif mode in ('min_color_tie','max_color_tie'):
        sign = 1 if mode=='min_color_tie' else -1
        chosen = min(objects,key=lambda o:(-len(o),sign*after[o[0][0]][o[0][1]],o[0]))
    elif mode == 'last_tie':
        chosen = max(objects,key=lambda o:(len(o),o[0]))
    elif mode == 'all_max':
        chosen = [cell for o in objects if len(o)==len(objects[0]) for cell in o]
    elif mode == 'all_winner_color':
        color = after[chosen[0][0]][chosen[0][1]]
        chosen = [[y,x] for y,row in enumerate(after) for x,val in enumerate(row) if val==color]
    elif mode in ('majority_color','minority_color','min_color','max_color'):
        key = (lambda x:sum(row.count(x) for row in g)) if mode in ('majority_color','minority_color') else lambda x:x
        color = (min if mode in ('minority_color','min_color') else max)((v,z),key=key)
        chosen = next(o for o in objects if after[o[0][0]][o[0][1]] == color)
    elif mode in ('horizontal','vertical'):
        candidates = [o for o in objects if len(o)>1 and
                      (len({p[0] for p in o})==1 if mode=='horizontal' else len({p[1] for p in o})==1)]
        chosen = candidates[0] if candidates else objects[0]
    elif mode != 'largest_fragment':
        raise ValueError(f'unknown policy {mode}')
    for y,x in chosen:
        if after[y][x] != 4:
            after[y][x] = 8
    return after


RIVALS = MODES + ('identity','diagonals','arms','modal_center','pre_ring',
    'smallest_fragment','second_fragment','last_tie','all_max','all_winner_color',
    'majority_color','minority_color','min_color','max_color','horizontal','vertical',
    'column_major_tie','min_color_tie','max_color_tie')


def _relay_program(*, wrong_order=False, tie="row"):
    # Alternate tie keys are explicit executable audit rivals, never settings.
    if tie not in ("row","column","min_color","max_color"):
        raise ValueError("unknown tie order")
    from puzzle_generators.rule_wrap import strip_rule_wrapper
    first = strip_rule_wrapper(LEGACY.instantiate_rule(4))
    inspected = 'g' if wrong_order else 'after'
    rowkey = '(+ (* 30 (apply min (map first (obj-cells o)))) (apply min (map second (obj-cells o))))'
    colkey = '(+ (* 30 (apply min (map second (obj-cells o)))) (apply min (map first (obj-cells o))))'
    key = colkey if tie=='column' else rowkey
    if tie in ('min_color','max_color'):
        key = f'(+ (* {1000 if tie == "min_color" else -1000} (obj-color o)) {rowkey})'
    return f'''(rule! (lambda (g)
      (let* ((after ({first} g))
             (candidates (filter (lambda (o) (!= (obj-color o) 4)) (objects {inspected} 0)))
             (ordered (sort-by candidates (lambda (o)
               (+ (* -100000 (length (obj-cells o))) {key}))))
             (chosen (obj-cells (first ordered))))
        (cellmap after (r c v)
          (if (and (!= v 4) (member (list r c) chosen)) 8 v)))))'''


def program(settings):
    mode = settings_mode(settings)
    if mode.startswith('frame_'):
        return LEGACY.instantiate_rule(int(mode[-1]))
    return _relay_program()


def counterfactual_program():
    return _relay_program(wrong_order=True)


def _bank(seed):
    rng = random.Random(f'cross-native:{seed}')
    lo,hi = sorted(rng.sample(PALETTE,2))
    h = rng.choice((16,18,20))
    # Minority total color wins a horizontal/vertical tie in row-major order.
    demos = [cross(h,h-2,4,2,hi,lo,1)]
    # Four equal arms, with opposite winning color rank, teach both tie policies.
    demos.append(cross(17,17,8,8,hi,lo,0))
    for index in range(2,6):
        rr = random.Random(f'cross-native:{seed}:extra:{index}')
        hh,ww = rr.randint(6,29), rr.randint(6,29)
        v,z = rr.sample(PALETTE,2)
        demos.append(cross(hh,ww,rr.randint(1,hh-2),rr.randint(1,ww-2),v,z,rr.randrange(2)))
    queries = []
    for index in range(4):
        rr = random.Random(f'cross-native:{seed}:query:{index}')
        hh,ww = ((4,4) if index==0 else (rr.randint(5,11),rr.randint(21,29)) if index==1
                 else (rr.randint(21,29),rr.randint(5,11)) if index==2 else (30,30))
        v,z = rr.sample(PALETTE,2)
        r,c = rr.randint(1,hh-2),rr.randint(1,ww-2)
        if index==3:
            r = rr.choice((1,28)); c = rr.choice((1,28))
        queries.append(cross(hh,ww,r,c,v,z,rr.randrange(2)))
    # No hidden resampling by setting; deterministic rare collisions fail loudly.
    grids = demos + queries
    if len({json.dumps(g) for g in grids}) != len(grids):
        raise ValueError('input bank collision')
    return demos,queries


def generate(seed, settings, demos=3, queries=4):
    mode = settings_mode(settings)
    _integer(seed,0,2**63-1,'seed'); _integer(demos,2,6,'demos'); _integer(queries,1,4,'queries')
    train,test = _bank(seed)
    pairs = lambda grids: [{'input':g, 'output':predict(g,mode)} for g in grids]
    return {'train':pairs(train[:demos]), 'test':pairs(test[:queries]),
            'program_solution':program(settings)}


def teaching_check(episode):
    checks = []
    for rival in RIVALS:
        refuted = [i for i,p in enumerate(episode['train']) if predict(p['input'],rival) != p['output']]
        different = [i for i,p in enumerate(episode['test']) if predict(p['input'],rival) != p['output']]
        checks.append({'rival':rival,'refuting_demos':refuted,'different_queries':different})
    return {'checks':checks,'ambiguous':[x for x in checks if not x['refuting_demos'] and x['different_queries']]}
