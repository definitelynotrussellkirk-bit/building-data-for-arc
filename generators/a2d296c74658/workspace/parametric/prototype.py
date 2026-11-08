"""Native orange-gap completion, optionally followed by yellow horizontal gaps.

Each stage reads its own complete input state. Native qualification, not this
Python mirror, executes and verifies every returned Racket label.
"""
from functools import lru_cache
import hashlib
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
SETTINGS = ({'completion_mode': 'vertical'}, {'completion_mode': 'cascade'})
DISTRACTORS = (1, 2, 3, 5, 6, 8, 9)


def _mode(settings):
    if type(settings) is not dict or set(settings) != {'completion_mode'}:
        raise ValueError('settings must contain exactly completion_mode')
    value = settings['completion_mode']
    if type(value) is not str or value not in ('vertical', 'cascade'):
        raise ValueError('completion_mode must be vertical or cascade')
    return value


def _grid(value):
    if type(value) is not list or not 1 <= len(value) <= 30 or type(value[0]) is not list:
        raise ValueError('grid must contain 1..30 list rows')
    width = len(value[0])
    if not 1 <= width <= 30 or any(type(row) is not list or len(row) != width for row in value):
        raise ValueError('grid must be rectangular, width 1..30')
    if any(type(v) is not int or not 0 <= v <= 9 for row in value for v in row):
        raise ValueError('cells must be exact integer ARC colors')
    return [row[:] for row in value]


def program(settings):
    mode = _mode(settings)
    return (HOME / ('canonical.rkt' if mode == 'vertical' else 'cascade.rkt')).read_text()


def first_stage(grid):
    original = _grid(grid)
    out = [row[:] for row in original]
    for r in range(1, len(original)-1):
        for c in range(len(original[0])):
            if original[r][c] == 0 and original[r-1][c] == original[r+1][c] == 7:
                out[r][c] = 4
    return out


def second_stage(grid):
    original = _grid(grid)
    out = [row[:] for row in original]
    for r in range(len(original)):
        for c in range(1, len(original[0])-1):
            if original[r][c] == 0 and original[r][c-1] == original[r][c+1] == 4:
                out[r][c] = 2
    return out


def mirror(grid, settings):
    mode = _mode(settings)
    a = first_stage(grid)
    return a if mode == 'vertical' else second_stage(a)


def analyze(grid):
    original = _grid(grid)
    a = first_stage(original)
    b = second_stage(a)
    a_cells, b_cells, old_candidates = [], [], []
    enabled, suppressed, kinds = [], [], {'both_new': 0, 'mixed': 0, 'both_existing': 0}
    for r in range(len(original)):
        for c in range(len(original[0])):
            if a[r][c] != original[r][c]:
                a_cells.append([r, c])
            if 0 < c < len(original[0])-1:
                was = original[r][c] == 0 and original[r][c-1] == original[r][c+1] == 4
                now = b[r][c] != a[r][c]
                if was:
                    old_candidates.append([r, c])
                if was and not now:
                    suppressed.append([r, c])
                if now:
                    b_cells.append([r, c])
                    if not was:
                        enabled.append([r, c])
                    new_count = sum(original[r][k] != 4 for k in (c-1, c+1))
                    kinds[('both_existing', 'mixed', 'both_new')[new_count]] += 1
    return {'stage_a_cells': a_cells, 'stage_b_cells': b_cells,
            'newly_enabled_stage_b_cells': enabled, 'suppressed_stage_b_cells': suppressed,
            'original_stage_b_candidates': old_candidates, 'stage_b_anchor_roles': kinds}


def _rng(seed, label):
    value = hashlib.sha256(f'a2d296c74658/native/v1/{seed}/{label}'.encode()).digest()
    return random.Random(int.from_bytes(value, 'big'))


def reflect(grid, flip_vertical=False, flip_horizontal=False):
    result = [row[:] for row in grid]
    if flip_vertical:
        result.reverse()
    if flip_horizontal:
        result = [row[::-1] for row in result]
    return result


def _stamp(grid, tile, r0, c0):
    for r, row in enumerate(tile):
        for c, value in enumerate(row):
            grid[r0+r][c0+c] = value


def _tiles(rng):
    a = [[0] * 11 for _ in range(11)]
    for r in range(0, 11, 2):
        for c in range(0, 11, 2):
            a[r][c] = 7
    b = [[0] * 11 for _ in range(11)]
    for r in (0, 2, 4):
        for c in range(0, 11, 2):
            b[r][c] = 4
    clutter = rng.choice(DISTRACTORS)
    # A lawful B target with yellow vertical/diagonal neighbors, nonempty
    # outer anchor neighbors, and unrelated nearby colors.
    _stamp(b, [[clutter, clutter, clutter, clutter, clutter],
               [4, 4, 0, 4, 4],
               [clutter, 4, 4, 4, clutter]], 7, 0)
    c = [[0] * 11 for _ in range(11)]
    _stamp(c, [[7, 0, 7], [0, 0, 0], [7, 0, 7]], 0, 0)
    _stamp(c, [[0, 7, 0], [4, 0, 4], [0, 7, 0]], 0, 6)
    _stamp(c, [[0, 0, 7], [4, 0, 0], [0, 0, 7]], 6, 0)
    _stamp(c, [[7, 0, 0], [0, 0, 4], [7, 0, 0]], 6, 6)
    # A remains eligible with touching orange endpoints, lateral orange,
    # diagonal orange, and a third color next to its empty center.
    _stamp(c, [[7, 7, 7], [7, 0, clutter], [7, 7, 7]], 3, 3)
    c[2][4] = c[6][4] = 7
    d = [[0] * 11 for _ in range(11)]
    block, wrong = rng.sample(DISTRACTORS, 2)
    for (r, c0), value in {
        (0, 0): 7, (1, 0): block, (2, 0): 7,
        (0, 3): wrong, (2, 3): wrong,
        (0, 6): 7, (3, 6): 7,
        (6, 0): 4, (6, 1): block, (6, 2): 4,
        (8, 0): wrong, (8, 2): wrong,
        (5, 5): 4, (5, 8): 4,
        (0, 4): 7,
        (6, 5): 7, (8, 7): 7,
        (6, 3): 4, (8, 5): 4,
    }.items():
        d[r][c0] = value
    return [a, b, c, d]


def _contrast(seed):
    rng = _rng(seed, 'demo-contrast')
    h, w = 25 + rng.randrange(3), 27 + rng.randrange(3)
    grid = [[0] * w for _ in range(h)]
    tiles = _tiles(rng)
    rng.shuffle(tiles)
    r0, c0 = rng.randrange(h-24), rng.randrange(w-24)
    for tile, (r, c) in zip(tiles, ((0, 0), (0, 14), (14, 0), (14, 14))):
        tile = reflect(tile, bool(rng.getrandbits(1)), bool(rng.getrandbits(1)))
        _stamp(grid, tile, r0+r, c0+c)
    for r, c, value in ((0, 0, 7), (1, 0, 0), (2, 0, 7),
                        (h-3, w-1, 7), (h-2, w-1, 0), (h-1, w-1, 7),
                        (0, w-3, 4), (0, w-2, 0), (0, w-1, 4),
                        (h-1, 0, 4), (h-1, 1, 0), (h-1, 2, 4)):
        grid[r][c] = value
    return reflect(grid, bool(rng.getrandbits(1)), bool(rng.getrandbits(1)))


def _small(seed):
    rng = _rng(seed, 'demo-small')
    h, w = 9, 11
    grid = [[0] * w for _ in range(h)]
    offset = rng.randrange(3)
    for r in range(offset, offset+7, 2):
        grid[r][2] = grid[r][4] = 7
    r0 = rng.randrange(1, h-2)
    grid[r0][8] = grid[r0+2][8] = 7
    grid[r0+1][6] = 4
    grid[8][6] = grid[8][8] = grid[8][10] = 4
    grid[0][10] = rng.choice(DISTRACTORS)
    return reflect(grid, bool(rng.getrandbits(1)), bool(rng.getrandbits(1)))


def _dense(seed, label, h, w):
    rng = _rng(seed, label)
    grid = []
    for _ in range(h):
        row = []
        for _ in range(w):
            x = rng.random()
            row.append(0 if x < .46 else 7 if x < .76 else 4 if x < .90 else rng.choice(DISTRACTORS))
        grid.append(row)
    # Long shared-endpoint chains are interior, extend through the canvas, and
    # are deliberately not capped at the production curriculum's two gaps.
    for r in range(h):
        for c in (1, 3):
            grid[r][c] = 7 if r % 2 == 0 else 0
        grid[r][2] = 0
    for c in range(w):
        grid[h-2][c] = 4 if c % 2 == 0 else 0
    if h >= 15 and w >= 19:
        _stamp(grid, [[0, 0, 0, 0, 0], [0, 0, 7, 0, 0], [0, 4, 0, 4, 0],
                      [0, 0, 7, 0, 0], [0, 0, 0, 0, 0]], h//2-2, w//2-2)
    return reflect(grid, bool(rng.getrandbits(1)), bool(rng.getrandbits(1)))


@lru_cache(maxsize=32)
def _inputs(seed):
    demos = [_small(seed), _contrast(seed)]
    for i, (h, w) in enumerate(((11, 13), (17, 19), (23, 27), (27, 29)), 2):
        demos.append(_dense(seed, f'demo-{i}', h, w))
    profiles = [(7, 9), (15, 19), (24, 28), (30, 30)]
    _rng(seed, 'query-order').shuffle(profiles)
    queries = [_dense(seed, f'query-{h}-{w}', h, w) for h, w in profiles]
    frozen = tuple(tuple(tuple(row) for row in grid) for grid in demos + queries)
    if len(set(frozen)) != 10:
        raise RuntimeError('duplicate generated inputs')
    return frozen


def generate(seed, settings, demos=3, queries=4):
    _mode(settings)
    for name, value, lo, hi in (('seed', seed, 0, 2**63-1), ('demos', demos, 2, 6), ('queries', queries, 1, 4)):
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f'{name} must be an integer in {lo}..{hi}')
    grids = _inputs(seed)
    def pair(value):
        grid = [list(row) for row in value]
        return {'input': grid, 'output': mirror(grid, settings)}
    return {'train': [pair(g) for g in grids[:demos]],
            'test': [pair(g) for g in grids[6:6+queries]], 'program_solution': program(settings)}
