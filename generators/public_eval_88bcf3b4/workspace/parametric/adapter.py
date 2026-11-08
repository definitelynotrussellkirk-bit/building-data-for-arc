"""Straighten finite colored strands around input-derived obstacle silhouettes.

The Python implementation supplies claims, never reference authority. Every
released setting is independently executed by protected Racket. No original
fixtures, answers, or other task modules are imported at generation time.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

PARAMETER = 'strand_extent'
VALUES = ('source', 'plus_two')
DEFAULT = {PARAMETER: VALUES[0]}
RIVALS = ('opposite_extent', 'identity', 'bbox_contour', 'straight_diagonal',
          'retain_source', 'first_strand_only', 'length_bbox_area',
          'length_primary_span', 'cardinal_components', 'fixed_zero_background',
          'fixed_output_color', 'no_exit_turn')
DEMO_DIMS = ((18, 18), (28, 28), (16, 20), (22, 24), (26, 28), (30, 30))
QUERY_DIMS = ((14, 16), (20, 22), (26, 28), (30, 30))


def integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError('Expected a grid of at most 30x30')
    if any(type(row) is not list or len(row) != len(value[0])
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in value):
        raise ValueError('Expected rectangular exact integer colors 0..9')
    return deepcopy(value)


def settings(value):
    if type(value) is not dict or set(value) != {PARAMETER} or value[PARAMETER] not in VALUES:
        raise ValueError(f'Expected exactly {PARAMETER} in {VALUES}')
    return value[PARAMETER]


def program(setting):
    mode = settings(setting)
    text = Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
    anchor = '(define extra-length 0)'
    if text.count(anchor) != 1:
        raise ValueError('Canonical extent anchor changed')
    return text if mode == 'source' else text.replace(anchor, '(define extra-length 2)')


def components(g, background, cardinal=False):
    seen = set(); result = []
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1)) if cardinal else tuple(
        (a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b)
    for r, row in enumerate(g):
        for c, color in enumerate(row):
            if color == background or (r, c) in seen:
                continue
            cells = []; stack = [(r, c)]; seen.add((r, c))
            while stack:
                a, b = stack.pop(); cells.append([a, b])
                for dr, dc in steps:
                    p = a + dr, b + dc
                    if (0 <= p[0] < len(g) and 0 <= p[1] < len(row)
                            and p not in seen and g[p[0]][p[1]] == color):
                        seen.add(p); stack.append(p)
            result.append({'color': color, 'cells': sorted(cells)})
    return result


def derive(value, *, cardinal=False, background=None):
    g = grid(value); h, w = len(g), len(g[0])
    bg = Counter(v for row in g for v in row).most_common(1)[0][0] if background is None else background
    objs = components(g, bg, cardinal)
    cell_to_object = {tuple(p): i for i, o in enumerate(objs) for p in o['cells']}
    roles = []
    for i, obj in enumerate(objs):
        cells = obj['cells']
        if len(cells) < 2:
            continue
        for axis, bound in ((0, h), (1, w)):
            if len({p[1-axis] for p in cells}) != 1:
                continue
            lo = min(p[axis] for p in cells); hi = max(p[axis] for p in cells)
            if lo != 0 and hi != bound-1 or lo == 0 and hi == bound-1:
                continue
            direction = 1 if lo == 0 else -1
            tip = max(cells, key=lambda p: direction*p[axis])
            for side in (-1, 1):
                anchor = tip[:]; anchor[1-axis] += side
                j = cell_to_object.get(tuple(anchor))
                if j is None or j == i:
                    continue
                strand = objs[j]
                if not all(direction*(p[axis]-anchor[axis]) <= 0 for p in strand['cells']):
                    continue
                roles.append({'pole_index': i, 'source_index': j, 'axis': axis,
                              'direction': direction, 'side': side, 'anchor': anchor,
                              'length': len(strand['cells']), 'color': strand['color'],
                              'source_cells': strand['cells']})
    occupied_roles = {x[k] for x in roles for k in ('pole_index', 'source_index')}
    strands = []
    for role in roles:
        axis, direction, side, anchor = (role[k] for k in ('axis','direction','side','anchor'))
        candidates = []
        for i, obj in enumerate(objs):
            if i in occupied_roles:
                continue
            by_u = {}
            for p in obj['cells']:
                u = direction*(p[axis]-anchor[axis])
                by_u.setdefault(u, []).append(p[1-axis])
            if min(by_u) <= 0:
                continue
            contour = [[u, (min(xs) if side < 0 else max(xs))+side] for u,xs in sorted(by_u.items())]
            gap, edge = contour[0]
            if abs(edge-anchor[1-axis]) > gap:
                continue
            candidates.append((gap, abs(edge-anchor[1-axis]), i, contour))
        if not candidates:
            continue
        _, _, index, contour = min(candidates)
        strands.append({**role, 'obstacle_index': index, 'obstacle_cells': objs[index]['cells'],
                        'contour': contour})
    return {'background': bg, 'strands': strands}


def trace(record, extent, height, width, rival=None):
    axis, direction, side, anchor = (record[k] for k in ('axis','direction','side','anchor'))
    contour = dict(record['contour']); first, last = min(contour), max(contour)
    if rival == 'bbox_contour':
        fixed = min(contour.values()) if side < 0 else max(contour.values())
        contour = {u: fixed for u in contour}
    cells = record['source_cells']; length = len(cells)
    if rival == 'length_bbox_area':
        length = (max(p[0] for p in cells)-min(p[0] for p in cells)+1)*(max(p[1] for p in cells)-min(p[1] for p in cells)+1)
    if rival == 'length_primary_span':
        length = max(p[axis] for p in cells)-min(p[axis] for p in cells)+1
    length += 2 if extent == 'plus_two' else 0
    x = anchor[1-axis]; path = []
    for u in range(length):
        if u:
            if rival == 'straight_diagonal':
                x += side
            elif u < first:
                x += (contour[first] > x)-(contour[first] < x)
            elif u <= last:
                x = contour.get(u, x)
            elif rival != 'no_exit_turn':
                x -= side
        p = anchor[:]; p[axis] += direction*u; p[1-axis] = x
        if not (0 <= p[0] < height and 0 <= p[1] < width):
            break
        path.append(p)
    return path


def solve(value, extent='source', *, rival=None):
    g = grid(value)
    if extent not in VALUES or rival is not None and rival not in RIVALS:
        raise ValueError('Unknown extent or rival')
    if rival == 'identity':
        return g
    if rival == 'opposite_extent':
        extent = VALUES[1-VALUES.index(extent)]
    state = derive(g, cardinal=rival=='cardinal_components', background=0 if rival=='fixed_zero_background' else None)
    strands = state['strands'][:1] if rival=='first_strand_only' else state['strands']
    out = deepcopy(g)
    if rival != 'retain_source':
        for record in strands:
            for r,c in record['source_cells']:
                out[r][c] = state['background']
    for record in strands:
        color = 4 if rival == 'fixed_output_color' else record['color']
        for r,c in trace(record, extent, len(g), len(g[0]), rival):
            out[r][c] = color
    return out


def input_errors(value):
    try:
        g = grid(value); state = derive(g)
    except (ValueError, TypeError, IndexError) as error:
        return [str(error)]
    if not state['strands']:
        return ['No unambiguous pole/strand/obstacle relation']
    ids = [s['source_index'] for s in state['strands']]
    if len(set(ids)) != len(ids):
        return ['One strand assigned more than once']
    for s in state['strands']:
        contour = s['contour']
        if [u for u,_ in contour] != list(range(contour[0][0], contour[-1][0]+1)):
            return ['Obstacle has a missing primary-axis slice']
        if any(abs(a[1]-b[1]) > 1 for a,b in zip(contour,contour[1:])):
            return ['Obstacle profile jumps by more than one cell']
        if any(abs(a[0]-b[0]) > 1 or abs(a[1]-b[1]) > 1
               for a,b in zip(trace(s,'plus_two',len(g),len(g[0])),trace(s,'plus_two',len(g),len(g[0]))[1:])):
            return ['Nonlocal strand path']
    return []


def _rotate(g, times):
    for _ in range(times % 4):
        g = [list(row) for row in zip(*g[::-1])]
    return g


def _scene(h, w, rng, colors, twist=False):
    bg, pole, strand, obstacle = colors
    g = [[bg]*w for _ in range(h)]
    ar = h-4; pc = w-3; ac = pc-1
    for r in range(ar,h):
        g[r][pc] = pole
    # Monotone but bent, with several cells in the same primary-axis slice.
    length = min(ar-1, rng.randint(6,9))
    cells = [(ar,ac)]; r,c = ar,ac
    for k in range(1,length):
        if k in (2,5) and r < h-1:
            r += 1
        else:
            c -= 1
            if rng.random() < .35 and r < h-1:
                r += 1
        cells.append((r,c))
    for r,c in cells:
        g[r][c] = strand
    bottom = ar-3; top = max(1,bottom-rng.randint(2,3))
    # Nonrectangular silhouette; same total cell count can have another contour.
    base = ac-2
    for r in range(top,bottom+1):
        offset = -1 if r == bottom-1 else 0
        width = rng.randint(1,3)
        for c in range(base+offset, min(w-1,base+offset+width)):
            g[r][c] = obstacle
    if twist:
        g = [row[::-1] for row in g]
    return g


def sample(seed, stream, index, attempt=0):
    integer(seed,0,2**63-1,'seed'); integer(attempt,0,4095,'attempt')
    if stream not in ('demo','query'):
        raise ValueError('Unknown stream')
    dims = DEMO_DIMS if stream == 'demo' else QUERY_DIMS
    integer(index,0,len(dims)-1,'index'); h,w = dims[index]
    rng = random.Random(f'strand-v1:{seed}:{stream}:{index}:{attempt}')
    bg = rng.choice(tuple(range(10)))
    palette = rng.sample([c for c in range(10) if c != bg], 6)
    multi = (stream=='demo' and index==1) or (stream=='query' and index==3) or index>=4
    if not multi:
        g = _scene(h,w,rng,[bg,*palette[:3]],bool(rng.getrandbits(1)))
        g = _rotate(g,rng.randrange(4))
    else:
        # Four isolated local scenes, anchored to the four actual canvas edges.
        # Reuse colors across roles; color aggregation is deliberately invalid.
        g = [[bg]*w for _ in range(h)]
        bounds = ((0,0,h//2,w//2,1), (0,w//2,h//2,w-w//2,2),
                  (h//2,0,h-h//2,w//2,0), (h//2,w//2,h-h//2,w-w//2,3))
        for i,(r0,c0,hh,ww,rot) in enumerate(bounds):
            sh,sw = (ww,hh) if rot%2 else (hh,ww)
            colors = [bg,palette[i%6],palette[(i+1)%6],palette[(i+3)%6]]
            tile = _rotate(_scene(sh,sw,rng,colors,False),rot)
            for r,row in enumerate(tile):
                g[r0+r][c0:c0+ww] = row
    return g


def survivors(train, setting):
    extent = settings(setting)
    return ['intended']+[name for name in RIVALS if all(
        solve(p['input'],extent,rival=name)==p['output'] for p in train)]


@lru_cache(maxsize=64)
def teaching(seed):
    for attempt in range(128):
        pair = [sample(seed,'demo',i,attempt) for i in range(2)]
        if all(survivors([{'input':g,'output':solve(g,extent)} for g in pair],{PARAMETER:extent})==['intended'] for extent in VALUES):
            return tuple(tuple(tuple(row) for row in g) for g in pair)
    raise ValueError('Bounded teaching search could not refute retained rivals')


def generate(seed, setting, demos, queries):
    integer(seed,0,2**63-1,'seed'); extent = settings(setting)
    integer(demos,2,6,'demos'); integer(queries,1,4,'queries')
    first = [list(map(list,g)) for g in teaching(seed)]
    demos_in = first+[sample(seed,'demo',i) for i in range(2,demos)]
    queries_in = [sample(seed,'query',i) for i in range(queries)]
    pairs = lambda gs: [{'input':g,'output':solve(g,extent)} for g in gs]
    return {'train':pairs(demos_in),'test':pairs(queries_in),'program_solution':program(setting)}


def public_view(episode, query_index):
    integer(query_index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':grid(p['input']),'output':grid(p['output'])} for p in episode['train']],
            'test':[{'input':grid(episode['test'][query_index]['input'])}]}


def presentation_order(presentation_seed):
    integer(presentation_seed,0,2**63-1,'presentation seed')
    order = list(range(4)); random.Random(f'strand-presentation-v1:{presentation_seed}').shuffle(order)
    return order


def public_turns(seed,setting,demos,presentation_seed=0,count=4):
    integer(count,1,4,'presentation count'); integer(presentation_seed,0,2**63-1,'presentation seed')
    episode = generate(seed,setting,demos,4)
    return [public_view(episode,i) for i in presentation_order(seed ^ presentation_seed)[:count]]
