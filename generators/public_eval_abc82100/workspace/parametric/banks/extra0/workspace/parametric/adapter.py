"""Directional stencil legends and post-stamp component selection.

Native resources are self-contained. Python supplies deterministic claims;
preflight/audit execute independent protected-Racket labels. No official data
is read by generation. The input stream is independent of the episode setting.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
PARAMETERS = {'component_policy': ['all_stamps', 'largest_component']}
DEFAULT = {'component_policy': 'all_stamps'}
RIVALS = ('all_stamps', 'largest_template', 'most_color', 'most_seeds',
          'first_component', 'last_component', 'smallest_component', 'three_copies')
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))


def _setting(settings):
    if (type(settings) is not dict or set(settings) != set(PARAMETERS)
            or type(settings['component_policy']) is not str
            or settings['component_policy'] not in PARAMETERS['component_policy']):
        raise ValueError('settings must name exactly one declared component_policy')
    return settings['component_policy']


def program(settings):
    policy = _setting(settings)
    source = (HERE / 'canonical.rkt').read_text()
    return source if policy == 'all_stamps' else source.replace(
        '(define output-policy "all_stamps")',
        f'(define output-policy "{policy}")', 1)


def rival_programs():
    source = program(DEFAULT)
    result = {name: source.replace('(define output-policy "all_stamps")',
            f'(define output-policy "{name}")', 1) for name in RIVALS}
    result['three_copies'] = result['three_copies'].replace(
        '(else (obj-cells (pick-max parts obj-size)))',
        '''(else (apply append
           (map obj-cells
            (filter (lambda (o)
              (for/or ((d defs))
                (and (= (obj-color o) (second d))
                     (= (obj-size o) (* 3 (length (mask d))))))) parts))))''')
    return result


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('expected rectangular 1..30 exact-integer color grid')
    return tuple(tuple(row) for row in grid)


def components(grid, diagonal=False):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    result = []
    directions = tuple((a, b) for a in (-1, 0, 1) for b in (-1, 0, 1)
                       if (a or b) and (diagonal or abs(a) + abs(b) == 1))
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        todo, cells = [first], {first}
        color = grid[first[0]][first[1]]
        while todo:
            r, c = todo.pop()
            for dr, dc in directions:
                point = r + dr, c + dc
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append(sorted(cells))
    return result


@lru_cache(maxsize=512)
def _analyze(frozen):
    h, w = len(frozen), len(frozen[0])
    gray = [{p for p in cells} for cells in components(frozen, True)
            if frozen[cells[0][0]][cells[0][1]] == 8]
    definitions = []
    for r in range(h):
        for c in range(w):
            old = frozen[r][c]
            if old in (0, 8):
                continue
            for dr, dc in DIRECTIONS:
                near = r + dr, c + dc
                origin = r + 2 * dr, c + 2 * dc
                if not (0 <= origin[0] < h and 0 <= origin[1] < w):
                    continue
                new = frozen[near[0]][near[1]]
                if new in (0, 8, old) or frozen[origin[0]][origin[1]] not in (0, 8):
                    continue
                for index, cells in enumerate(gray):
                    if any(max(abs(a-origin[0]), abs(b-origin[1])) <= 1 for a, b in cells):
                        definitions.append(dict(source=old, dest=new, old=(r,c),
                            near=near, origin=origin, direction=(dr,dc), component=index))
    def distance(point, definition):
        r,c = point; a,b = definition['origin']; dr,dc = definition['direction']
        return abs((r-a)*dc-(c-b)*dr)
    for definition in definitions:
        competitors = [d for d in definitions if d['component'] == definition['component']]
        definition['mask'] = sorted(p for p in gray[definition['component']]
            if distance(p,definition) == min(distance(p,d) for d in competitors))
    erased = {p for cells in gray for p in cells}
    erased.update(p for d in definitions for p in (d['old'],d['near']))
    sources = {d['source'] for d in definitions}
    out = [[0 if (r,c) in erased or value in sources else value
            for c,value in enumerate(row)] for r,row in enumerate(frozen)]
    for d in definitions:
        d['seeds'] = [(r,c) for r in range(h) for c in range(w)
                      if (r,c) not in erased and frozen[r][c] == d['source']]
        for r,c in d['seeds']:
            for mr,mc in d['mask']:
                rr,cc = r+mr-d['origin'][0], c+mc-d['origin'][1]
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = d['dest']
    return {'definitions':definitions, 'output':out, 'components':components(out)}


def analyze(grid):
    """Fresh author-private intermediate certificate, not a public payload."""
    return deepcopy(_analyze(_grid(grid)))


def predict(grid, policy='all_stamps'):
    if policy not in RIVALS + ('largest_component',):
        raise ValueError('undeclared prediction policy')
    info = _analyze(_grid(grid))
    out = deepcopy(info['output'])
    parts = info['components']
    if policy == 'all_stamps' or not parts:
        return out
    if policy == 'most_color':
        colors = sorted({v for row in out for v in row if v})
        target = max(colors, key=lambda v:sum(row.count(v) for row in out))
        selected = [(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v == target]
    elif policy in ('largest_template','most_seeds'):
        metric = 'mask' if policy == 'largest_template' else 'seeds'
        if not info['definitions']:
            return out
        target = max(info['definitions'],key=lambda d:len(d[metric]))['dest']
        selected = [(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v == target]
    elif policy == 'three_copies':
        selected = [p for cells in parts
                    if any(out[cells[0][0]][cells[0][1]] == d['dest']
                           and len(cells) == 3*len(d['mask']) for d in info['definitions'])
                    for p in cells]
    elif policy == 'first_component':
        selected = parts[0]
    elif policy == 'last_component':
        selected = parts[-1]
    elif policy == 'smallest_component':
        selected = min(parts,key=len)
    else:
        selected = max(parts,key=len)
    for r,c in selected:
        out[r][c] = 9
    return out


def _transform(grid, rotation, reflected):
    result = deepcopy(grid)
    if reflected:
        result = [row[::-1] for row in result]
    for _ in range(rotation):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _scene(seed, index):
    rng = random.Random(f'abc82100:inputs:v1:{seed}:{index}')
    sizes = [(18,22),(20,24),(21,25),(24,26),(25,27),(26,28),
             (22,24),(24,27),(28,29),(30,30)]
    h,w = sizes[index]
    grid = [[0]*w for _ in range(h)]
    palette = list(range(1,8));rng.shuffle(palette)
    sources = palette[:2]
    dests = palette[2:4] if index%2==0 else list(reversed(sources))
    unrelated = palette[4]
    # Both masks have a complete transverse spine. Copies at stride three
    # become connected after stamping, although their source markers do not.
    spine = {(1,0),(1,1),(1,2),(0,1),(2,1)}
    corners = [(0,0),(0,2),(2,0),(2,2)];rng.shuffle(corners)
    small = sorted(spine)
    large = sorted(spine | set(corners[:3]))
    winner = index%2
    masks = [small,large] if winner==0 else [large,small]
    for i,mask in enumerate(masks):
        r0,c0 = 2,3+10*i
        grid[r0-2][c0] = sources[i]
        grid[r0-1][c0] = dests[i]
        for r,c in mask:
            grid[r0+r][c0+c] = 8
    if index==9:
        group = [(13,2+3*k) for k in range(5)]
        singles = [(r,c) for r in (7,20,25) for c in (2,8,20,27)]
        singles += [(29,6),(29,16),(18,29),(21,0)]
    else:
        group_row, single_row = (7,h-6) if index%2==0 else (h-5,7)
        group = [(group_row,2+3*k) for k in range(3 if index%2==0 else 4)]
        singles = [(single_row,c) for c in (1,6,11,16)]
        if index%2:
            singles.append((h-8,w-4))
        # A clipped corner copy is a useful query boundary case, not padding.
        if index>=6:
            singles += [(h-1,w-2),(h-5,w-1)]
    for r,c in group:
        grid[r][c] = sources[winner]
    for r,c in singles:
        grid[r][c] = sources[1-winner]
    # Unmapped singleton landmarks distinguish preservation and positional rules.
    for r,c in ((0,0),(0,w-1),(h-1,0),(h-1,w-1)):
        grid[r][c] = unrelated
    result = _transform(grid,rng.randrange(4),bool(rng.randrange(2)))
    info = analyze(result)
    if len(info['definitions']) != 2:
        raise ValueError('constructive scene lost its two unique legend stems')
    sizes_after = [len(c) for c in info['components']]
    if sizes_after.count(max(sizes_after)) != 1:
        raise ValueError('construction lacks a unique largest stamped component')
    return result


@lru_cache(maxsize=128)
def _bank(seed):
    return tuple(_scene(seed,index) for index in range(10))


def generate(seed, settings, demos=3, queries=4):
    policy = _setting(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('seed must be an integer in 0..2**63-1')
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError('demos must be an integer in 2..6')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('queries must be an integer in 1..4')
    bank = _bank(seed)
    permutation = list(range(4))
    random.Random(f'abc82100:presentation:v1:{seed}').shuffle(permutation)
    def pair(index):
        grid = deepcopy(bank[index])
        return {'input':grid, 'output':predict(grid,policy)}
    return {'train':[pair(i) for i in range(demos)],
            'test':[pair(6+i) for i in permutation[:queries]],
            'program_solution':program(settings),
            'private':{'settings':deepcopy(settings),'seed':seed,'query_permutation':permutation}}


def public_turn(episode, index=0):
    if type(index) is not int or not 0 <= index < len(episode['test']):
        raise ValueError('query index out of range')
    return {'train':[{'input':deepcopy(p['input']), 'output':deepcopy(p['output'])}
                     for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
