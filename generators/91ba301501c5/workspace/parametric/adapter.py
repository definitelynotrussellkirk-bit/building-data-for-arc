"""Ray-induced region selection; standalone native adapter, no runtime side effects."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
from pathlib import Path
import random

TASK = '91ba301501c5'
PARAMETER = 'region_policy'
SETTINGS = ('rays_only', 'largest_region')
RIVALS = ('rays_only', 'smallest_region', 'first_region', 'last_region',
          'input_region', 'all_regions', 'both_toward', 'both_away')
CANONICAL = Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {'region_policy'}:
        raise ValueError('settings must contain exactly region_policy')
    value = settings['region_policy']
    if type(value) is not str or value not in SETTINGS:
        raise ValueError('unknown region_policy')
    return value


def _rng(seed, role):
    return random.Random(int.from_bytes(hashlib.sha256(f'{TASK}:v1:{seed}:{role}'.encode()).digest(), 'big'))


def regions(grid):
    """Four-connected zero components, ordered by their first row-major cell."""
    h, w = len(grid), len(grid[0])
    unseen = {(r,c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue, cells = deque([start]), []
        while queue:
            r,c = queue.popleft()
            cells.append((r,c))
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in unseen:
                    unseen.remove(p)
                    queue.append(p)
        result.append(sorted(cells))
    return result


def rays(grid, mode='canonical'):
    h, w = len(grid), len(grid[0])
    dividers = [r for r,row in enumerate(grid) if all(v == 5 for v in row)]
    if len(dividers) != 1:
        raise ValueError('expected one full gray divider')
    d = dividers[0]
    result = deepcopy(grid)
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v not in (1,2):
                continue
            away = v == 1
            if mode == 'both_toward': away = False
            if mode == 'both_away': away = True
            dr = (-1 if r < d else 1) * (1 if away else -1)
            rr = r + dr
            while 0 <= rr < h and grid[rr][c] == 0:
                result[rr][c] = v
                rr += dr
    return result


def predict(grid, mode):
    if mode not in {*SETTINGS, *RIVALS}:
        raise ValueError(f'unknown rule: {mode}')
    base = rays(grid, mode)
    if mode == 'rays_only':
        return base
    parts = regions(grid if mode == 'input_region' else base)
    if not parts:
        return base
    if mode == 'smallest_region': selected = min(parts, key=len)
    elif mode == 'first_region': selected = parts[0]
    elif mode == 'last_region': selected = parts[-1]
    else: selected = max(parts, key=len)
    if mode == 'all_regions':
        selected = [p for part in parts for p in part]
    for r,c in selected:
        if base[r][c] == 0:
            base[r][c] = 8
    return base


def rule(mode):
    """Native setting and executable adversarial rules; all return one rule!."""
    if mode not in {*SETTINGS, *RIVALS}:
        raise ValueError(f'unknown rule: {mode}')
    if mode == 'rays_only':
        return CANONICAL
    ray_callable = CANONICAL[len('(rule! '):-1]
    if mode == 'both_toward':
        ray_callable = ray_callable.replace('((and (= v 1) above) -1)', '((and (= v 1) above) 1)').replace('((and (= v 1) (not above)) 1)', '((and (= v 1) (not above)) -1)')
    elif mode == 'both_away':
        ray_callable = ray_callable.replace('((and (= v 2) above) 1)', '((and (= v 2) above) -1)').replace('(else -1)', '(else 1)')
    inspected = 'g' if mode == 'input_region' else 'base'
    selector = {'smallest_region':'(pick-min parts length)', 'first_region':'(car parts)',
                'last_region':'(last parts)'}.get(mode, '(pick-max parts length)')
    cells = 'chosen'
    if mode == 'all_regions':
        cells = '(apply append parts)'
    return f'''(rule! (lambda (g)
      (let* ((base ({ray_callable} g))
             (parts (sort (map (lambda (xs) (sort xs cell<)) (find-0-regions {inspected} 0))
                          (lambda (a b) (cell< (car a) (car b))))))
        (if (null? parts) base
            (let* ((chosen {selector}) (cells {cells})
                   (empty-cells (filter (lambda (p) (= (at base (first p) (second p)) 0)) cells)))
              (recolor-cells base empty-cells 8))))))'''


def program(settings):
    return rule(_setting(settings))


def _candidate(rng, h, w):
    d = rng.randrange(3, h-3)
    grid = [[0]*w for _ in range(h)]
    grid[d] = [5]*w
    for above in (True, False):
        # Boundary red seeds become complete walls only after ray completion.
        wall_count = 4 if w >= 24 else 2
        walls = sorted(rng.sample(range(1,w-1), wall_count))
        boundary = 0 if above else h-1
        for c in walls:
            grid[boundary][c] = 2
        free = [c for c in range(w) if c not in walls]
        rng.shuffle(free)
        count = min(len(free), 8 if w >= 24 else (5 if w >= 14 else 3))
        for i,c in enumerate(free[:count]):
            color = 1 if i % 2 == 0 else 2
            if color == 1:
                row = rng.randrange(1,d) if above else rng.randrange(d+1,h-1)
            else:
                row = rng.randrange(0,d-1) if above else rng.randrange(d+2,h)
            grid[row][c] = color
    return grid


def _scene(seed, role, dims):
    rng = _rng(seed, role)
    h,w = dims
    for attempt in range(256):
        grid = _candidate(rng,h,w)
        base = rays(grid)
        parts = regions(base)
        lengths = sorted((len(p) for p in parts), reverse=True)
        if len(parts) < 4 or lengths[0] == lengths[1]:
            continue
        target = predict(grid, 'largest_region')
        # The two-demo minimum is constructive at episode level: each retained
        # scene already refutes the explicitly bounded nearby rule bank.
        if any(predict(grid, m) == target for m in RIVALS):
            continue
        if h == w == 30 and sum(base[r][c] != grid[r][c] for r in range(h) for c in range(w)) < 60:
            continue
        return grid
    raise RuntimeError(f'no distinguishing scene after 256 candidates: {seed}/{role}/{dims}')


@lru_cache(maxsize=64)
def _inputs(seed):
    demos = [_scene(seed, f'demo-{i}', dims) for i,dims in enumerate(
        ((10,10),(12,14),(14,10),(16,18),(18,16),(20,22)))]
    specs = [(10,14),(17,22),(24,27),(30,30)]
    _rng(seed,'query-order').shuffle(specs)
    queries = [_scene(seed,f'query-{i}',dims) for i,dims in enumerate(specs)]
    return demos, queries


def generate(seed, settings, demos=3, queries=4):
    _integer(seed,0,2**63-1,'seed')
    _integer(demos,2,6,'demos')
    _integer(queries,1,4,'queries')
    mode = _setting(settings)
    train, test = _inputs(seed)
    def pair(g):
        return {'input':deepcopy(g), 'output':predict(g,mode)}
    return {'train':[pair(g) for g in train[:demos]],
            'test':[pair(g) for g in test[:queries]],
            'program_solution':program(settings)}


def public_turn(episode, index):
    """Projection only, not a controller: reveal a single supplied query index."""
    _integer(index,0,len(episode['test'])-1,'query index')
    return deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                     'test':[{'input':episode['test'][index]['input']}]})
