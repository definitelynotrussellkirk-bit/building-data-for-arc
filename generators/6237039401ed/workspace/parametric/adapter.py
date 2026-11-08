"""Recolor cells by complete-window participation, from an immutable input.

This richer grammar is separate from the unchanged production sampler.
"""
from hashlib import sha256
from pathlib import Path
from functools import lru_cache
import random

SETTINGS = [{'window_size': n, 'minimum_overlap': k} for n in (2, 3) for k in (1, 2)]
RIVALS = ('component_area_ge4', 'all_gray', 'whole_eligible_component',
          'solid_rectangles_only', 'paint_during_detection',
          'maximum_rectangle_rule', 'maximum_rectangle_mask')


def setting(value):
    if (type(value) is not dict or set(value) != {'window_size', 'minimum_overlap'}
            or type(value['window_size']) is not int or value['window_size'] not in (2, 3)
            or type(value['minimum_overlap']) is not int or value['minimum_overlap'] not in (1, 2)):
        raise ValueError('Expected window_size=2|3 and minimum_overlap=1|2 as exact integers')
    return value['window_size'], value['minimum_overlap']


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError('Grid must be rectangular, 1..30, with exact integer colors0..9')


def program(settings):
    n, minimum = setting(settings)
    if (n, minimum) == (2, 1):
        return Path(__file__).with_name('canonical.rkt').read_text()
    return _program(n, minimum, scan=False)


def scan_rival_program(settings):
    n, minimum = setting(settings)
    return _program(n, minimum, scan=True)


def _program(n, minimum, *, scan):
    helpers = f'''(define (solid-at? scene r0 c0)
      (and (>= r0 0) (<= (+ r0 {n}) h)
           (>= c0 0) (<= (+ c0 {n}) w)
           (for*/and ([dr (in-range {n})] [dc (in-range {n})])
             (= (at scene (+ r0 dr) (+ c0 dc)) 5))))
    (define (memberships scene r c)
      (for*/sum ([dr (in-range {n})] [dc (in-range {n})])
        (if (solid-at? scene (- r dr) (- c dc)) 1 0)))'''
    if not scan:
        body = f'''(cellmap g (r c v)
      (if (and (= v 5) (>= (memberships g r c) {minimum})) 1 v))'''
    else:
        body = f'''(for*/fold ([scene g]) ([r (in-range h)] [c (in-range w)])
      (let ([eligible (and (= (at scene r c) 5)
                           (>= (memberships scene r c) {minimum}))])
        (cellmap scene (rr cc v)
          (if (and eligible (= rr r) (= cc c)) 1 v))))'''
    return '(rule! (let ()\n    ' + helpers + '\n    ' + body + '))'


def membership_counts(grid, n):
    """Accumulate every complete original window before changing any cell."""
    h, w = len(grid), len(grid[0]); counts = [[0]*w for _ in range(h)]
    for r in range(h-n+1):
        for c in range(w-n+1):
            if all(grid[rr][cc] == 5 for rr in range(r, r+n) for cc in range(c, c+n)):
                for rr in range(r, r+n):
                    for cc in range(c, c+n):
                        counts[rr][cc] += 1
    return counts


def transform(grid, settings):
    n, minimum = setting(settings); validate_grid(grid)
    counts = membership_counts(grid, n)
    return [[1 if v == 5 and counts[r][c] >= minimum else v
             for c, v in enumerate(row)] for r, row in enumerate(grid)]


def scan_rival(grid, settings):
    n, minimum = setting(settings); validate_grid(grid)
    result = [row[:] for row in grid]; h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            count = sum(all(result[rr][cc] == 5 for rr in range(r0, r0+n) for cc in range(c0, c0+n))
                        for r0 in range(max(0, r-n+1), min(r, h-n)+1)
                        for c0 in range(max(0, c-n+1), min(c, w-n)+1))
            if result[r][c] == 5 and count >= minimum:
                result[r][c] = 1
    return result


def components(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5}
    result = []
    while remaining:
        start = min(remaining); remaining.remove(start); stack = [start]; found = {start}
        while stack:
            r, c = stack.pop()
            for p in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if p in remaining:
                    remaining.remove(p); found.add(p); stack.append(p)
        result.append(found)
    return result


@lru_cache(maxsize=4096)
def _maximum_rectangles(cells):
    cells = frozenset(cells); h = max(r for r,c in cells)+1; w = max(c for r,c in cells)+1
    best, rectangles = 0, []
    for r0 in range(h):
        for r1 in range(r0+1,h+1):
            for c0 in range(w):
                for c1 in range(c0+1,w+1):
                    area = (r1-r0)*(c1-c0)
                    if area < best or not all((r,c) in cells for r in range(r0,r1) for c in range(c0,c1)):
                        continue
                    if area > best: best, rectangles = area, []
                    rectangles.append((r0,r1,c0,c1))
    return tuple(rectangles)


def rival_output(grid, settings, name):
    n, minimum = setting(settings)
    if name == 'paint_during_detection':
        return scan_rival(grid, settings)
    if name not in RIVALS:
        raise ValueError('Undeclared rival')
    counts = membership_counts(grid, n); out = [row[:] for row in grid]
    for cells in components(grid):
        if name in ('maximum_rectangle_rule', 'maximum_rectangle_mask'):
            lo_r = min(r for r,c in cells); lo_c = min(c for r,c in cells)
            normalized = tuple(sorted((r-lo_r,c-lo_c) for r,c in cells))
            for r0,r1,c0,c1 in _maximum_rectangles(normalized):
                if name == 'maximum_rectangle_rule':
                    cropped = transform([[5]*(c1-c0) for _ in range(r1-r0)],settings)
                for r in range(r0,r1):
                    for c in range(c0,c1):
                        if ((name == 'maximum_rectangle_rule' and cropped[r-r0][c-c0] == 1)
                                or (name == 'maximum_rectangle_mask' and counts[r+lo_r][c+lo_c] >= minimum)):
                            out[r+lo_r][c+lo_c] = 1
            continue
        if name == 'component_area_ge4':
            paint = len(cells) >= 4
        elif name == 'all_gray':
            paint = True
        else:
            eligible = any(counts[r][c] >= minimum for r,c in cells)
            if name == 'whole_eligible_component':
                paint = eligible
            else:
                rows, cols = zip(*cells)
                paint = eligible and len(cells) == (max(rows)-min(rows)+1)*(max(cols)-min(cols)+1)
        if paint:
            for r,c in cells: out[r][c] = 1
    return out


def _rng(seed, domain, index):
    raw = f'6237039401ed:{domain}:{seed}:{index}'.encode()
    return random.Random(int.from_bytes(sha256(raw).digest(), 'big'))


def _rectangle(h, w):
    return {(r,c) for r in range(h) for c in range(w)}


def _orient(cells, rng):
    for _ in range(rng.randrange(4)):
        cells = {(-c,r) for r,c in cells}
    low_r = min(r for r,c in cells); low_c = min(c for r,c in cells)
    return {(r-low_r,c-low_c) for r,c in cells}


def scene(seed, domain, index, h, w):
    rng = _rng(seed, domain, index)
    # Positives, overlapping-window boundaries, tailed positives and large
    # negatives share every scene grammar; placement never reveals the setting.
    shapes = [_rectangle(2,2), _rectangle(3,3), _rectangle(4,4) | {(4,1)},
              {(0,0),(0,1),(0,2),(1,1)},
              {(r,c) for r in range(5) for c in range(5) if r in (0,4) or c in (0,4)},
              _rectangle(4,4) | {(2,4),(3,4),(4,1),(4,2),(4,3),(4,4)}]
    slots = [(r,c) for r in range(0,h-4,6) for c in range(0,w-4,6)]
    rng.shuffle(slots)
    # Small queries keep an overlapping positive plus both kinds of contrast.
    if len(slots) < 6:
        shapes = [shapes[2], shapes[1], shapes[3], shapes[0]]
    while len(shapes) < len(slots):
        if rng.randrange(2):
            cells = _rectangle(rng.randint(2,5), rng.randint(2,5))
            if rng.randrange(2):
                cells.discard((0,0))
        else:
            r = c = 2; cells = {(r,c)}
            for _ in range(rng.randint(3,22)):
                dr,dc = rng.choice(((1,0),(-1,0),(0,1),(0,-1)))
                r = min(4,max(0,r+dr)); c = min(4,max(0,c+dc)); cells.add((r,c))
        shapes.append(cells)
    grid = [[0]*w for _ in range(h)]
    for (r0,c0), cells in zip(slots, shapes):
        cells = _orient(cells, rng)
        r0 += rng.randrange(5-max(r for r,c in cells))
        c0 += rng.randrange(5-max(c for r,c in cells))
        for r,c in cells: grid[r0+r][c0+c] = 5
    if rng.randrange(2): grid.reverse()
    if rng.randrange(2): grid = [row[::-1] for row in grid]
    return grid


def teaching_check(episode, settings):
    setting(settings)
    demos = episode['train']
    survivors = [s for s in SETTINGS if all(transform(p['input'],s) == p['output'] for p in demos)]
    rivals = [name for name in RIVALS if all(rival_output(p['input'],settings,name) == p['output'] for p in demos)]
    return {'survivors': survivors, 'surviving_rivals': rivals,
            'scope': 'Four declared settings and seven named rivals; demonstrations only.'}


def generate(seed, settings, demos=2, queries=4):
    setting(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('Seed must be an exact integer in0..2^63-1')
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError('Demonstrations must be2..6')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('Queries must be1..4')
    demo_sizes = [(12,18),(18,18),(12,24),(18,24),(24,24),(18,30)]
    query_sizes = [(12,14),(18,20),(24,29),(30,30)]
    _rng(seed,'query_size_order',0).shuffle(query_sizes)
    def pairs(domain, sizes):
        result = []
        for i,(h,w) in enumerate(sizes):
            grid = scene(seed, domain, i, h, w)
            result.append({'input':grid,'output':transform(grid,settings)})
        return result
    episode = {'train':pairs('demo',demo_sizes[:demos]),
               'test':pairs('query',query_sizes[:queries]),'program_solution':program(settings)}
    check = teaching_check(episode, settings)
    if check['survivors'] != [settings] or check['surviving_rivals']:
        raise ValueError('Demonstrations failed the declared teaching contrasts')
    return episode
