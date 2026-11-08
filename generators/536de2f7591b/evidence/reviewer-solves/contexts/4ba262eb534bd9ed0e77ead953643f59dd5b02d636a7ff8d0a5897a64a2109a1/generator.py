"""Row-local left sliding of contiguous green blocks; inputs only.

Canonical suffix blocks have lengths one or two. The defended extension also
includes length three, interior blocks and inert path distractors. Labels remain
owned by the unchanged Racket authority. Four consecutive default samples cover
canonical support and the three explicitly declared canonical-fitting rivals.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = '536de2f7591b'
TASK_ID = GENERATOR_ID
RULE_HASH = '02c227b9b2a6'
VERSION = '3.0.1'
SUMMARY = (
    'Slide each contiguous color-3 row block left until immediately after the '
    'nearest color-8 cell originally to its left, or column zero. Preserve block '
    'length. Other rows and all 8s stay fixed. Optional nonmarker distractors '
    'are placed outside both initial and final block footprints and survive.'
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20
INVARIANTS = [
    'rectangular integer grid, 5..18 rows and 6..20 columns, colors 0..9',
    'at least one green row, each with one contiguous block of length 1..3',
    'at least one cyan wall and one background cell; no cap on cyan cells per row',
    'distractors never occupy initial or final green footprints',
    'interior blocks and cyan cells to their right are lawful extensions',
]
AXES = {
    'grid_h': {'type': 'int', 'default': 'canonical/band mixture', 'valid': '5..18'},
    'grid_w': {'type': 'int', 'default': 'canonical/band mixture', 'valid': '6..20'},
    'n_green_rows': {'type': 'int', 'default': '2..4', 'valid': '1..6'},
    'max_block_width': {'type': 'int', 'default': '1..3 by profile', 'valid': '1..3'},
    'n_distractors': {'type': 'int', 'default': '0 except path profile 1..3', 'valid': '0..3'},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [('grid_h', 'n_green_rows')]
SCHEDULE_PROFILES = ('canonical_suffix', 'interior', 'path_distractor', 'wide_block')


def schedule_profile(seed, sample_index, difficulty=None):
    """Coverage schedule, not an independently configurable semantic axis."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _dimension(ctx, name, limits, preferred):
    lo, hi = limits
    # Overrides use the entire documented domain in every difficulty band.
    return ctx.draw_choice(name, list(range(lo, hi + 1)) + list(preferred) * 30)


def _blocks(grid):
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value == 3]
        if cols:
            yield r, cols[0], len(cols)


def _destination(row, start):
    return 1 + max((c for c in range(start) if row[c] == 8), default=-1)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f'unknown override axes: {sorted(unknown)}')
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f'{name} must be an integer')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError(f'unknown difficulty: {difficulty!r}')
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    bands = {'easy': ((5, 6, 7), (6, 7, 8)),
             'medium': ((7, 9, 11), (8, 10, 12)),
             'hard': ((13, 15, 18), (14, 17, 20))}
    hp, wp = bands[difficulty or 'medium']
    minimum_h = max(5, overrides.get('n_green_rows') or 1)
    if profile in ('canonical_suffix', 'wide_block'):
        # Half of default samples retain exact canonical canvas profiles.
        # Shapes are sampled jointly, but all explicit dimensions remain free.
        shape = ctx.draw_choice('canonical_shape', [(7, 6), (7, 8), (9, 8), (9, 9)])
        h = (ctx.draw_int('grid_h', 5, 18) if overrides.get('grid_h') is not None
             else ctx.draw_choice('grid_h', [shape[0]]))
        w = (ctx.draw_int('grid_w', 6, 20) if overrides.get('grid_w') is not None
             else ctx.draw_choice('grid_w', [shape[1]]))
    else:
        # A lone n_green_rows=6 override is feasible; an explicit grid_h=5
        # combination is rejected below instead of clipping either control.
        lo = 5 if overrides.get('grid_h') is not None else minimum_h
        h = _dimension(ctx, 'grid_h', (lo, 18), [v for v in hp if v >= lo] or [lo])
        w = _dimension(ctx, 'grid_w', (6, 20), wp)
    count = ctx.draw_choice('n_green_rows', list(range(1, 7)) + [2, 3, 4] * 20)
    if count > h:
        if overrides.get('n_green_rows') is not None:
            raise ValueError('n_green_rows cannot exceed grid_h')
        count = ctx.draw_choice('n_green_rows', list(range(1, min(6, h) + 1)))
    default_width = 3 if profile == 'wide_block' else 2
    widths = [1, 2, 3] + [default_width] * 80
    # The canonical component is deliberately strict, without restricting an
    # explicit width override in that component.
    if profile == 'canonical_suffix' and overrides.get('max_block_width') is None:
        widths = [1, 2, 2, 2]
    if profile == 'path_distractor' and overrides.get('max_block_width') is None:
        widths = [1, 2, 2, 2]
    maximum = ctx.draw_choice('max_block_width', widths)
    distractors = ctx.draw_choice('n_distractors', [0, 1, 2, 3] if overrides.get('n_distractors') is not None
                                  else ([1, 2, 3] if profile == 'path_distractor' else [0]))
    rng = ctx.draw_rng('layout')
    rows = rng.sample(range(h), count)
    lengths = [maximum] + [rng.randint(1, min(2, maximum)) for _ in rows[1:]]
    # A wide-block profile supplies its rival witness on EVERY default draw.
    if profile == 'wide_block' and overrides.get('max_block_width') is None:
        maximum = ctx.draw_choice('max_block_width', [3])
        lengths[0] = maximum
    grid = full_grid(h, w, 0)
    forbidden_walls, footprints = set(), set()
    path_cell = None
    for i, (r, length) in enumerate(zip(rows, lengths)):
        start = w - length
        if profile == 'interior' and i == 0:
            start = rng.randint(1, w - length - 1)
        elif profile != 'canonical_suffix' and i > 0 and rng.random() < 0.35:
            start = rng.randint(1, w - length)
        # Always move the first block. Other rows include stationary blocks.
        stop = rng.randint(-1 if i != 1 else 0, start - 2 if i == 0 else start - 1)
        if profile == 'path_distractor' and path_cell is None and w >= 2 * length + 1:
            start, stop = w - length, -1
            path_cell = (r, length)  # beyond destination, before initial block
        dest = stop + 1
        for c in range(start, start + length):
            grid[r][c] = 3
        if stop >= 0:
            grid[r][stop] = 8
        forbidden_walls.update((r, c) for c in range(dest, start))
        footprints.update((r, c) for c in range(dest, dest + length))
        if profile == 'interior' and i == 0:
            grid[r][w - 1] = 8  # a right-side wall must NOT block left motion
    # Reserve all distractors before filling wall texture, without replacement.
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] == 0 and (r, c) not in footprints]
    chosen = [path_cell] if distractors and path_cell in candidates else []
    chosen += rng.sample([p for p in candidates if p not in chosen], distractors - len(chosen))
    for r, c in chosen:
        grid[r][c] = rng.choice((1, 2, 4, 5, 6, 7, 9))
    wall_slots = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] == 0 and (r, c) not in forbidden_walls]
    density = ctx.draw_rng('wall_density').uniform(0.20, 0.45)
    wall_count = max(1, round(len(wall_slots) * density)) if wall_slots else 0
    for r, c in rng.sample(wall_slots, wall_count):
        grid[r][c] = 8
    if not any(8 in row for row in grid):
        raise RuntimeError('constructive wall placement has no lawful slot')
    return grid


def observe_overrides(grid):
    blocks = list(_blocks(grid))
    return {'grid_h': len(grid), 'grid_w': len(grid[0]),
            'n_green_rows': len(blocks),
            'max_block_width': max((length for _, _, length in blocks), default=0),
            'n_distractors': sum(v not in (0, 3, 8) for row in grid for v in row)}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ['expected a nonempty rectangular grid']
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ['ragged grid']
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ['expected integer colors 0..9 (not bool)']
    errors = []
    if not (5 <= h <= 18 and 6 <= w <= 20):
        errors.append('dimensions outside declared domain')
    colors = {v for row in grid for v in row}
    if not {0, 3, 8} <= colors:
        errors.append('missing background, green block or cyan wall')
    for r, start, length in _blocks(grid):
        cols = [c for c, v in enumerate(grid[r]) if v == 3]
        if length > 3 or cols != list(range(start, start + length)):
            errors.append(f'row {r}: expected one contiguous green block of length 1..3')
            continue
        dest = _destination(grid[r], start)
        if any(grid[r][c] not in (0, 3) for c in range(dest, dest + length)):
            errors.append(f'row {r}: destination would overwrite a nonmarker distractor')
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if any(v not in (0, 3, 8) for row in grid for v in row):
        errors.append('extended palette')
    if any(start + length != len(grid[0]) or length > 2 for _, start, length in _blocks(grid)):
        errors.append('canonical component requires suffix blocks of length one or two')
    return errors


def _rival(grid, mode):
    """Explicit WRONG hypotheses, never used as generation labels."""
    out = [list(row) for row in grid]
    for r, start, length in _blocks(grid):
        if mode == 'suffix_only' and start + length != len(grid[0]):
            continue
        stops = [c for c in range(start) if (grid[r][c] != 0 if mode == 'any_nonzero_barrier' else grid[r][c] == 8)]
        dest = max(stops, default=-1) + 1
        for c in range(start, start + length):
            out[r][c] = 0
        for c in range(dest, dest + (min(2, length) if mode == 'width_at_most_two' else length)):
            out[r][c] = 3
    return out


def _suffix_only(grid):
    return _rival(grid, 'suffix_only')


def _any_nonzero_barrier(grid):
    return _rival(grid, 'any_nonzero_barrier')


def _width_at_most_two(grid):
    return _rival(grid, 'width_at_most_two')


def _moving_interior(grid):
    return any(start + length < len(grid[0]) and _destination(grid[r], start) < start
               for r, start, length in _blocks(grid))


def _path_distractor(grid):
    return any(any(grid[r][c] not in (0, 3, 8) for c in range(_destination(grid[r], start), start))
               for r, start, _ in _blocks(grid))


def _wide_block(grid):
    return any(length == 3 for _, _, length in _blocks(grid))


SEMANTIC_RIVALS = {'suffix_only': _suffix_only, 'any_nonzero_barrier': _any_nonzero_barrier,
                   'width_at_most_two': _width_at_most_two}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {'moving_interior': _moving_interior, 'path_distractor': _path_distractor,
                      'wide_block': _wide_block}
WITNESS_RIVALS = {'moving_interior': ['suffix_only'], 'path_distractor': ['any_nonzero_barrier'],
                  'wide_block': ['width_at_most_two']}
