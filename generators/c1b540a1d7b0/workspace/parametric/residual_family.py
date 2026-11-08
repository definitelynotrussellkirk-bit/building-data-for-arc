"""Native residual-room family; claim labels are independently replayed in Racket.

This module intentionally bypasses the production sampler's canonical bitmap
branch. It reuses only its constructive room/bridge/tip builder and rule mirror.
All random draws are independent of settings and requested prefix lengths.
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
    '_residual_rooms_base_' + hashlib.sha256(str(HOME).encode()).hexdigest()[:12],
    HOME.parents[1] / 'generator.py')
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
CANONICAL = (HOME / 'canonical.rkt').read_text(encoding='utf-8')
SETTINGS = ('all_rooms', 'largest_room')
RIVALS = ('all_rooms', 'first_room', 'last_room', 'smallest_room', 'all_cyan',
          'pre_arm_largest')
DIRS = ((-1, 0), (0, -1), (1, 0), (0, 1))


def _policy(settings: dict) -> str:
    if (type(settings) is not dict or set(settings) != {'room_policy'}
            or type(settings['room_policy']) is not str
            or settings['room_policy'] not in SETTINGS):
        raise ValueError('settings must contain exactly room_policy=all_rooms|largest_room')
    return settings['room_policy']


def components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    """Four-connected, same-color components in row-major discovery order."""
    left = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color}
    result = []
    while left:
        first = min(left)
        left.remove(first)
        part, stack = {first}, [first]
        while stack:
            r,c = stack.pop()
            for dr,dc in DIRS:
                q = r+dr,c+dc
                if q in left:
                    left.remove(q)
                    part.add(q)
                    stack.append(q)
        result.append(part)
    return result


def _thick_mask(grid):
    h,w = len(grid),len(grid[0])
    thick = set()
    for r in range(h-1):
        for c in range(w-1):
            block = {(r,c),(r+1,c),(r,c+1),(r+1,c+1)}
            if all(grid[a][b] == 5 for a,b in block):
                thick.update(block)
    return [[8 if (r,c) in thick else 0 for c in range(w)] for r in range(h)]


def transform(grid: list[list[int]], policy: str) -> list[list[int]]:
    """Deterministic claim interpreter. Not an authoritative label service."""
    if policy not in set(SETTINGS) | set(RIVALS):
        raise ValueError('unknown room policy')
    stage = _base.rule_mirror(grid)
    if policy == 'all_rooms':
        return stage
    regions = components(_thick_mask(grid) if policy == 'pre_arm_largest' else stage, 8)
    if not regions:
        return stage
    if policy == 'first_room':
        selected = regions[0]
    elif policy == 'last_room':
        selected = regions[-1]
    elif policy == 'smallest_room':
        selected = min(regions,key=len)
    elif policy == 'all_cyan':
        selected = set().union(*regions)
    else:
        selected = max(regions,key=len)
    # A wrong pre-removal intermediate still feeds the identical final paint
    # operation: only cells surviving as cyan can be selected for recoloring.
    return [[3 if (r,c) in selected and v == 8 else v
             for c,v in enumerate(row)] for r,row in enumerate(stage)]


@lru_cache(maxsize=None)
def rule_for(policy: str) -> str:
    """Canonical setting is exact source; alternatives compose its execution."""
    if policy not in set(SETTINGS) | set(RIVALS):
        raise ValueError('unknown room policy')
    if policy == 'all_rooms':
        return CANONICAL
    stage = wrap_rule(CANONICAL)
    if policy == 'pre_arm_largest':
        region_grid = '''(grid-from-fn (rows g) (cols g)
          (lambda (r c)
            (if (for*/or ((dr (list -1 0)) (dc (list -1 0)))
                  (let ((a (+ r dr)) (b (+ c dc)))
                    (and (>= a 0) (>= b 0) (< (+ a 1) (rows g))
                         (< (+ b 1) (cols g))
                         (= (cell-at g a b) 5) (= (cell-at g (+ a 1) b) 5)
                         (= (cell-at g a (+ b 1)) 5)
                         (= (cell-at g (+ a 1) (+ b 1)) 5)))) 8 0)))'''
    else:
        region_grid = 'stage'
    choose = {'first_room':'(first regions)', 'last_room':'(last regions)',
              'smallest_room':'(pick-min regions obj-size)'}.get(policy, '(pick-max regions obj-size)')
    selected = '(apply append (map obj-cells regions))' if policy == 'all_cyan' else f'(obj-cells {choose})'
    return f'''(rule! (lambda (g)
      ;; A: decompose gray rooms/arms using the exact canonical rule.
      ;; B: select a residual room by occupied area, then paint it green.
      (let* ((stage ({stage} g))
             (regions (filter (lambda (o) (= (obj-color o) 8)) (objects {region_grid} 0))))
        (if (null? regions) stage
          (recolor-cells stage
            (filter (lambda (p) (= (cell-at stage (first p) (second p)) 8))
                    {selected}) 3)))))'''


def program(settings: dict) -> str:
    return rule_for(_policy(settings))


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f'residual-rooms-v1:{seed}:{label}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def describe(grid: list[list[int]]) -> dict:
    cells = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 5]
    sizes = [len(part) for part in components(_base.rule_mirror(grid),8)]
    h,w = len(grid),len(grid[0])
    return {'shape':[h,w], 'gray_cells':len(cells), 'residual_sizes':sizes,
            'span':[max(r for r,c in cells)-min(r for r,c in cells)+1,
                    max(c for r,c in cells)-min(c for r,c in cells)+1] if cells else [0,0],
            'quadrants':[sum((r >= h//2)*2+(c >= w//2) == q for r,c in cells) for q in range(4)]}


def _scene(rng: random.Random, h: int, w: int, rooms: int, tips: int,
           *, stress: bool = False) -> list[list[int]]:
    for _ in range(256):
        grid = _base._build_blob(rng,h,w,rooms,tips)
        if grid is None:
            continue
        info = describe(grid)
        sizes = info['residual_sizes']
        if len(sizes) < 2 or sizes.count(max(sizes)) != 1:
            continue
        if stress and (info['gray_cells'] < 150 or min(info['span']) < 26
                       or min(info['quadrants']) < 15 or len(sizes) < 20):
            continue
        return grid
    raise RuntimeError(f'bounded constructive sampler exhausted for {h}x{w}/{rooms} rooms')


def _stress_scene(rng: random.Random) -> list[list[int]]:
    """Four fresh room networks, anchored to opposite corners without padding.

    Construct coverage separately from the global unique-winner condition.
    Every quadrant contains seven rooms and genuine arm interactions; only one
    quadrant retains a six-cell room. Its location is independently shuffled.
    The extended large grammar admits four blobs (small scenes use one).
    """
    tiles = []
    for role in range(4):
        for _ in range(128):
            tile = _base._build_blob(rng,14,14,7,2 if role == 0 else 6)
            if tile is None:
                continue
            sizes = describe(tile)['residual_sizes']
            if ((role == 0 and max(sizes) == 6 and sizes.count(6) == 1)
                    or (role > 0 and max(sizes) <= 4)):
                tiles.append(tile)
                break
        else:
            raise RuntimeError('bounded stress tile construction exhausted')
    rng.shuffle(tiles)
    grid = [[0]*30 for _ in range(30)]
    for quadrant,tile in enumerate(tiles):
        cells = [(r,c) for r,row in enumerate(tile) for c,v in enumerate(row) if v == 5]
        r0,r1 = min(r for r,c in cells),max(r for r,c in cells)
        c0,c1 = min(c for r,c in cells),max(c for r,c in cells)
        dr = -r0 if quadrant < 2 else 29-r1
        dc = -c0 if quadrant % 2 == 0 else 29-c1
        for r,c in cells:
            grid[r+dr][c+dc] = 5
    return grid


@lru_cache(maxsize=64)
def _inputs(seed: int) -> tuple:
    # Select a two-example teaching set from fresh constructive layouts, never
    # canonical exemplars. All later examples/queries use separate RNG streams.
    rng = _rng(seed,'teaching')
    candidates = []
    remaining = set(RIVALS)
    demos = []
    seen = set()
    for _ in range(32):
        grid = _scene(rng, rng.randint(10,14), rng.randint(13,18),
                      rng.randint(4,6),rng.randint(2,6))
        key = tuple(map(tuple,grid))
        if key in seen:
            continue
        seen.add(key)
        correct = transform(grid,'largest_room')
        rejects = {name for name in RIVALS if transform(grid,name) != correct}
        candidates.append((grid,rejects))
        if len(rejects) == len(RIVALS):
            break
    for _ in range(2):
        if not candidates:
            break
        index = max(range(len(candidates)),key=lambda i:len(candidates[i][1] & remaining))
        grid, rejects = candidates.pop(index)
        demos.append(grid)
        remaining.difference_update(rejects)
    # One strong demonstration is sufficient for the bounded rivals, but the
    # interface always supplies at least two independent demonstrations.
    if remaining:
        raise RuntimeError('two demonstrations did not distinguish: '+','.join(sorted(remaining)))
    while len(demos) < 6:
        slot = len(demos)
        r = _rng(seed,f'demo-{slot}')
        for attempt in range(32):
            grid = _scene(r,10+slot,14+slot,4+(slot%3),2+(slot%4))
            key = tuple(map(tuple,grid))
            if key not in {tuple(map(tuple,x)) for x in demos}:
                demos.append(grid)
                break
        else:
            raise RuntimeError('distinct demonstration budget exhausted')
    queries = []
    for slot, spec in enumerate(((8,10,3,2),(16,22,7,5),(22,28,12,8),(30,30,28,8))):
        r = _rng(seed,f'query-{slot}')
        for _ in range(32):
            grid = _stress_scene(r) if slot == 3 else _scene(r,*spec)
            if tuple(map(tuple,grid)) not in {tuple(map(tuple,x)) for x in demos+queries}:
                queries.append(grid)
                break
        else:
            raise RuntimeError('distinct query budget exhausted')
    return tuple(tuple(tuple(row) for row in g) for g in demos), tuple(tuple(tuple(row) for row in g) for g in queries)


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    policy = _policy(settings)
    if type(seed) is not int:
        raise ValueError('seed must be an exact integer')
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError('demos must be an exact integer in 2..6')
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError('queries must be an exact integer in 1..4')
    train,test = _inputs(seed)
    def pair(raw):
        grid = [list(row) for row in raw]
        return {'input':grid,'output':transform(grid,policy)}
    return {'train':[pair(g) for g in train[:demos]],
            'test':[pair(g) for g in test[:queries]],'program_solution':program(settings)}


def public_turn(episode: dict, query_index: int) -> dict:
    """Fresh single-query projection; the controller owns all private fields."""
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('query_index must identify one stored query')
    return {'train':deepcopy([{'input':p['input'],'output':p['output']} for p in episode['train']]),
            'test':[{'input':deepcopy(episode['test'][query_index]['input'])}]}
