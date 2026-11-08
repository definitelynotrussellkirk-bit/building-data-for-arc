"""Count-selected nested-frame band fill (canonical H72 / 0f075657ddbb).

Only zero cells in the selected yellow-frame band become cyan. Red cells in
row 0 select the band; red elsewhere, other colors, and existing cyan survive.
A missing/out-of-range selector or absent frames is a lawful identity branch.
The Racket program is the label authority; rule_mirror is a diagnostic oracle.
"""
from __future__ import annotations

from hashlib import blake2s

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = '0f075657ddbb'
TASK_ID = GENERATOR_ID
VERSION = '3.0.1'
RULE_HASH = '99635e96d174'
ALLOW_IDENTITY_OUTPUT = True  # Canonical train[2] and test[0] are identity pairs.
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    'Nested yellow rectangular frames with row-0 red-count selection. Exact '
    'size/count/gap/palette controls; translated and offset stacks; scattered '
    'selectors, lawful no-ops, off-row red and protected in-band clutter.'
)
INVARIANTS = [
    'integer colors 0..9 on a rectangular grid no larger than 30x30',
    'background 0 and at least two foreground colors (scene grammar, not full program domain)',
    'every color-4 component is a complete rectangular perimeter',
    'frames are strictly nested and separated by at least one blank-cell gap',
    'only row-0 color-2 cells determine k; out-of-range k means no change',
    'only zero cells in the selected band are painted 8; nonzeros are preserved',
]
PALETTE_KINDS = ('default', 'warm', 'cool', 'varied')
DEGENERATE_TEXTURES = ('no_frames', 'no_markers', 'single_frame')
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
HELPFUL_TEXTURES = PALETTE_KINDS
AXES = {
    'grid_h': {'type': 'int', 'default': 'feasible band-aware 11..30', 'valid': '11..30'},
    'grid_w': {'type': 'int', 'default': 'feasible band-aware 11..30', 'valid': '11..30'},
    'n_frames': {'type': 'int', 'default': '2..5; texture can request 0 or 1', 'valid': '0..5'},
    'band_gap': {'type': 'int', 'default': '2..3', 'valid': '2..3',
                 'doc': 'Minimum per-side inset. Exact for >=2 frames; reject explicit use with <2.'},
    'k_select': {'type': 'int', 'default': 'four-profile cycle: three active, seed-conditioned missing/overflow', 'valid': '0..6'},
    'palette_size': {'type': 'int', 'default': 'compact 2..3, broad 2..4 foreground colors', 'valid': '2..6',
                     'doc': 'Exact number of distinct nonzero INPUT colors, not including background.'},
    'position_bias': {'type': 'enum', 'default': 'concentric|offset', 'valid': 'concentric|offset',
                      'doc': 'offset has an asymmetric inset; requires at least two frames.'},
    'texture': {'type': 'enum', 'default': 'default|warm|cool|varied',
                'valid': 'default|warm|cool|varied|no_frames|no_markers|single_frame',
                'doc': 'Palette preferences apply to distractors, never to semantic colors 0/2/4/8.'},
}
# Static semantic conflicts plus structured geometry errors below. No generic
# catch-all rejection declaration: unsupported combinations remain falsifiable.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {'texture':'no_frames', 'n_frames':[1,2,3,4,5]},
    {'texture':'single_frame', 'n_frames':[0,2,3,4,5]},
    {'texture':'no_markers', 'k_select':[1,2,3,4,5,6]},
    {'n_frames':[0,1], 'band_gap':None},
    {'n_frames':[0,1], 'position_bias':'offset'},
    {'texture':['no_frames','single_frame'], 'band_gap':None},
    {'texture':['no_frames','single_frame'], 'position_bias':'offset'},
]
SCHEDULE_PROFILES = (0,1,2,3)


class IncompatibleOverrides(ValueError):
    """A rejected joint request, with the actual participating pinned axes."""
    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def _seed_phase(seed):
    return int.from_bytes(blake2s(str(int(seed)).encode(),digest_size=8).digest(),'big')


def schedule_profile(seed, sample_index, difficulty=None):
    """Four indices contain first, last, random-rank and one no-op example.

    Each seed fixes its no-op regime (missing OR overflow), so four demos
    refute every listed rival that could change a query from that same seed.
    Across seeds both no-op regimes occur. Independent seed mixing avoids the
    (seed+index)%N alias for production callers using (i,i).
    """
    del difficulty
    return (_seed_phase(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)


def _shape_errors(grid):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ['grid must be a nonempty list of row lists']
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ['grid must be nonempty and rectangular']
    if len(grid) > 30 or len(grid[0]) > 30:
        return ['grid exceeds 30x30']
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ['grid cells must be integer colors 0..9 (not booleans)']
    return []


def _components_of_color(grid, color):
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    components = []
    while pending:
        start = min(pending)
        pending.remove(start)
        todo, cells = [start], {start}
        while todo:
            r, c = todo.pop()
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in pending:
                    pending.remove(p)
                    cells.add(p)
                    todo.append(p)
        components.append(cells)
    return components


def _frames(grid):
    boxes, errors = [], []
    for cells in _components_of_color(grid, 4):
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        border = {(r, c) for r in range(r0, r1+1) for c in range(c0, c1+1)
                  if r in (r0, r1) or c in (c0, c1)}
        if r0 == r1 or c0 == c1 or cells != border:
            errors.append(f'color-4 component at {(r0,c0,r1,c1)} is not a rectangular frame')
        else:
            boxes.append((r0, c0, r1, c1))
    boxes.sort(key=lambda b: (-(b[2]-b[0]+1)*(b[3]-b[1]+1), b[0], b[1]))
    return boxes, errors


def _gaps(boxes):
    return [(b[0]-a[0], b[1]-a[1], a[2]-b[2], a[3]-b[3])
            for a, b in zip(boxes, boxes[1:])]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check scene geometry, not whether the selector happens to trigger a fill."""
    del difficulty, meta
    errors = _shape_errors(grid)
    if errors:
        return errors
    boxes, frame_errors = _frames(grid)
    errors.extend(frame_errors)
    if any(min(gap) < 2 for gap in _gaps(boxes)):
        errors.append('frames must be strictly nested with separated perimeters')
    if any(box[0] == 0 for box in boxes):
        errors.append('frame stack must leave row 0 for selectors')
    colors = {v for row in grid for v in row}
    if 0 not in colors or len(colors - {0}) < 2:
        errors.append('scene requires background 0 and at least two foreground colors')
    return errors


def _band_cells(grid, boxes, k):
    if not 1 <= k <= len(boxes):
        return []
    t, l, b, r = boxes[k-1]
    inner = boxes[k] if k < len(boxes) else None
    return [(y, x) for y in range(t+1, b) for x in range(l+1, r)
            if grid[y][x] != 4 and not (inner and inner[0] < y < inner[2] and inner[1] < x < inner[3])]


def rule_mirror(grid):
    """Pure, task-local diagnostic mirror; training labels must still use Racket."""
    errors = self_check(grid)
    if errors:
        raise ValueError('; '.join(errors))
    out = [row[:] for row in grid]
    boxes, _ = _frames(grid)
    k = sum(v == 2 for v in grid[0])
    for r, c in _band_cells(grid, boxes, k):
        if grid[r][c] == 0:
            out[r][c] = 8
    return out


def _draw_exact_int(ctx, name, value, lo, hi):
    if name in ctx.overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, value, value)


def _draw_exact_choice(ctx, name, value, choices):
    if name in ctx.overrides:
        return ctx.draw_choice(name, choices)
    return ctx.draw_choice(name, (value,))


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f'unknown override axes: {unknown}')
    limits = {'grid_h': (11,30), 'grid_w': (11,30), 'n_frames': (0,5),
              'band_gap': (2,3), 'k_select': (0,6), 'palette_size': (2,6)}
    for key, value in overrides.items():
        if key in limits:
            lo, hi = limits[key]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f'{key} must be an integer in {lo}..{hi}, got {value!r}')
        elif not isinstance(value, str) or value not in AXES[key]['valid'].split('|'):
            raise ValueError(f'invalid {key}: {value!r}')


def _frame_outline(grid, top, left, bottom, right, color=4):
    for c in range(left, right+1):
        grid[top][c] = color
        grid[bottom][c] = color
    for r in range(top, bottom+1):
        grid[r][left] = color
        grid[r][right] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct a feasible scene once; infeasible pinned combinations raise.

    No retry/fallback, clipping, global RNG, runtime labels or canonical-grid
    lookup is used. Keyed provenance records every exact observable axis.
    """
    _validate_overrides(overrides)
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('difficulty must be easy, medium, hard, or None')
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng('layout:' + (difficulty or 'medium'))
    profile = schedule_profile(seed, sample_index, difficulty)
    texture = _draw_exact_choice(ctx, 'texture', rng.choice(PALETTE_KINDS),
                                 PALETTE_KINDS + DEGENERATE_TEXTURES)
    forced_n = 0 if texture == 'no_frames' else 1 if texture == 'single_frame' else None
    if forced_n is not None and overrides.get('n_frames', forced_n) != forced_n:
        raise IncompatibleOverrides(f'texture={texture} conflicts with n_frames', ('texture','n_frames'))
    if texture == 'no_markers' and overrides.get('k_select', 0) != 0:
        raise IncompatibleOverrides('texture=no_markers conflicts with k_select', ('texture','k_select'))

    # Enumerate only structural feasibility (24 tiny candidates), not instances.
    # Explicit axes filter this set before any stochastic layout selection.
    ns = [overrides['n_frames']] if 'n_frames' in overrides else (
        [forced_n] if forced_n is not None else list(range(2, 4 if difficulty == 'easy' else 6)))
    gaps = [overrides['band_gap']] if 'band_gap' in overrides else [2,3]
    biases = [overrides['position_bias']] if 'position_bias' in overrides else ['concentric','offset']
    feasible = []
    for nf in ns:
        for gap in gaps:
            for bias in biases:
                if nf < 2 and (bias == 'offset' or 'band_gap' in overrides):
                    continue
                # A 3x3 innermost frame ensures overflow differs from clamping.
                min_outer = 3 + 2 * gap * max(0, nf-1) if nf else 0
                extra = int(bias == 'offset')
                min_h, min_w = max(11, 1+min_outer+extra), max(11, min_outer)
                if min_h > overrides.get('grid_h',30) or min_w > overrides.get('grid_w',30):
                    continue
                feasible.append((nf,gap,bias,min_h,min_w))
    if not feasible:
        axes = [key for key in ('texture','n_frames','band_gap','position_bias','grid_h','grid_w')
                if key in overrides]
        raise IncompatibleOverrides('infeasible frame count, gap, layout and grid dimensions (or inactive band_gap)',axes)
    # Preserve canonical-scale morphology without replaying any example grid.
    # Compact scenes use a generic square/rectangle mixture; broad scenes retain
    # up to five frames, wider gaps, and difficulty-dependent larger canvases.
    compact_options = [item for item in feasible if item[3] <= 14 and item[4] <= 16]
    compact = bool(compact_options) and rng.random() < 0.65
    nf, gap, bias, min_h, min_w = rng.choice(compact_options if compact else feasible)
    nf = _draw_exact_int(ctx, 'n_frames', nf, 0, 5)
    gap = _draw_exact_int(ctx, 'band_gap', gap, 2, 3)
    bias = _draw_exact_choice(ctx, 'position_bias', bias, ('concentric','offset'))
    cap = {'easy':18, 'medium':26, 'hard':30, None:26}[difficulty]
    if compact:
        planned_h, planned_w = rng.randint(min_h,14), rng.randint(max(12,min_w),16)
        square_min = max(12,min_h,min_w)
        if 'grid_h' not in overrides and 'grid_w' not in overrides and square_min <= 14 and rng.random()<0.5:
            planned_h = planned_w = rng.randint(square_min,14)
    else:
        planned_h, planned_w = rng.randint(min_h,max(min_h,cap)), rng.randint(min_w,max(min_w,cap))
    h = _draw_exact_int(ctx, 'grid_h', planned_h, 11, 30)
    w = _draw_exact_int(ctx, 'grid_w', planned_w, 11, 30)
    if texture == 'no_markers':
        planned_k = 0
    elif texture in ('no_frames','single_frame'):
        planned_k = 1
    else:
        noop_k = 0 if (_seed_phase(seed) >> 2) & 1 else min(6,nf+1)
        planned_k = (1,nf,rng.randint(1,max(1,nf)),noop_k)[profile]
    k = _draw_exact_int(ctx, 'k_select', planned_k, 0, 6)

    grid = full_grid(h,w,0)
    boxes = []
    if nf:
        insets = [[gap]*4 for _ in range(nf-1)]
        if bias == 'offset':
            # One extra top inset breaks concentricity while retaining the exact
            # minimum gap and a predictable feasibility bound.
            insets[rng.randrange(nf-1)][0] += 1
        vertical = sum(x[0]+x[2] for x in insets)
        horizontal = sum(x[1]+x[3] for x in insets)
        oh = rng.randint(3+vertical,h-1)
        ow = rng.randint(3+horizontal,w)
        top = rng.randint(1,h-oh)
        left = rng.randint(0,w-ow)
        bottom, right = top+oh-1, left+ow-1
        for i in range(nf):
            boxes.append((top,left,bottom,right))
            _frame_outline(grid,top,left,bottom,right)
            if i < nf-1:
                dt,dl,db,dr = insets[i]
                top += dt; left += dl; bottom -= db; right -= dr
    # The first-rank profile visibly separates row counting from a prefix
    # shortcut in every four-demo lesson. Other profiles may use column 0.
    marker_columns = range(1,w) if profile == 0 else range(w)
    for c in rng.sample(marker_columns,k):
        grid[0][c] = 2

    # Foreground palette is exact. Semantic colors are never remapped.
    palette_size = _draw_exact_int(ctx, 'palette_size', rng.choice([2,3,3,3]) if compact else rng.randint(2,4), 2, 6)
    required = ({4} if nf else set()) | ({2} if k else {8})
    preferred = {
        'default': [6,7,5,8,9,1,3,2],
        'warm': [7,6,9,5,8,1,3,2],
        'cool': [1,3,8,5,6,7,9,2],
        'varied': [1,2,3,5,6,7,8,9],
    }.get(texture,[8,6,7,1,3,5,9,2])
    pool = [color for color in preferred if color not in required]
    # Keep each palette preference observable while still varying colors.
    if texture == 'varied':
        rng.shuffle(pool)
    else:
        first = pool[:2]
        rng.shuffle(first)
        pool = first + pool[2:]
    palette = sorted(required) + pool[:palette_size-len(required)]
    for color in palette:
        if any(color in row for row in grid):
            continue
        free = [(r,c) for r in range(h) for c in range(w)
                if grid[r][c] == 0 and (color != 2 or r > 0)]
        header = [p for p in free if p[0] < (boxes[0][0] if boxes else 2)]
        r,c = rng.choice(header or free)
        grid[r][c] = color
        # Small varied distractor clusters, with no frame or selector overwrite.
        for dr,dc in ((0,1),(1,0),(1,1)):
            if rng.random() < 0.5 and r+dr < h and c+dc < w and grid[r+dr][c+dc] == 0:
                if color != 2 or r+dr > 0:
                    grid[r+dr][c+dc] = color

    # An in-band red cell is BOTH a protected nonzero and an off-row selector
    # decoy. Keep some uncluttered cases rather than making clutter a new cue.
    band = [(r,c) for r,c in _band_cells(grid,boxes,k) if grid[r][c] == 0]
    if k and 2 in palette and len(band) > 1 and (profile in (0,1) or rng.random() < 0.5):
        r,c = rng.choice(band)
        grid[r][c] = 2
    errors = self_check(grid)
    if errors:
        raise AssertionError('constructor violated scene contract: ' + '; '.join(errors))
    return grid


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError('; '.join(errors))
    boxes, _ = _frames(grid)
    result = {'grid_h':len(grid), 'grid_w':len(grid[0]), 'n_frames':len(boxes),
              'k_select':sum(v == 2 for v in grid[0]),
              'palette_size':len({v for row in grid for v in row} - {0}),
              'position_bias':'offset' if any(len(set(gap)) > 1 for gap in _gaps(boxes)) else 'concentric'}
    if len(boxes) >= 2:
        result['band_gap'] = min(min(gap) for gap in _gaps(boxes))
    return result


def strict_canonical_like(grid):
    return self_check(grid)


def _rival(grid, mode):
    errors = self_check(grid)
    if errors:
        raise ValueError('; '.join(errors))
    boxes, _ = _frames(grid)
    k = sum(v == 2 for v in grid[0])
    if mode == 'all_red':
        k = sum(v == 2 for row in grid for v in row)
    elif mode == 'prefix':
        k = 0
        for v in grid[0]:
            if v != 2:
                break
            k += 1
    elif mode == 'clamp' and k and boxes:
        k = min(k,len(boxes))
    out = [row[:] for row in grid]
    for r,c in _band_cells(grid,boxes,k):
        if grid[r][c] == 0 or mode == 'overwrite':
            out[r][c] = 8
    return out


SEMANTIC_RIVALS = {
    'count_all_red': lambda g: _rival(g,'all_red'),
    'count_leading_red_prefix': lambda g: _rival(g,'prefix'),
    'overwrite_nonzero_band_cells': lambda g: _rival(g,'overwrite'),
    'clamp_out_of_range_selector': lambda g: _rival(g,'clamp'),
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(grid, name):
    if self_check(grid):
        return False
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    name: (lambda grid, rival=name: _refutes(grid,rival)) for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name:[name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """A finite-rival diagnostic, not a proof against all possible programs."""
    errors = []
    for i,pair in enumerate(demos):
        if self_check(pair['input']) or rule_mirror(pair['input']) != pair.get('output'):
            errors.append(f'demo {i} is malformed or disagrees with the task rule')
    if self_check(query['input']):
        return errors + ['query is outside the nested-frame scene grammar']
    answer = rule_mirror(query['input'])
    if query.get('output') is not None and query['output'] != answer:
        errors.append('query label disagrees with the task rule')
    if errors:
        return errors
    for name,rival in LESSON_COMPETITORS.items():
        if all(rival(p['input']) == p['output'] for p in demos) and rival(query['input']) != answer:
            errors.append(f'{name} fits all demos but changes the query answer')
    return errors
