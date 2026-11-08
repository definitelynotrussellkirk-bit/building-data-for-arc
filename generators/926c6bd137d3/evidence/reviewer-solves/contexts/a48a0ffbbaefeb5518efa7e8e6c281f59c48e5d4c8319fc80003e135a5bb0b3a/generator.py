"""Yellow frames filled by their own marker; labels remain Racket-owned.

Every four consecutive default draws include two rich contrasts. Holding out
one pair still leaves a demonstration of the declared semantic distinctions.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = '926c6bd137d3'
TASK_ID = GENERATOR_ID
VERSION = '3.0.0'
RULE_HASH = '575c55ee70e4'
SUMMARY = ('Fill blank interiors of hollow yellow rectangles with each frame\'s '
           'singleton marker color. Preserve borders, markers and exterior '
           'objects. Marker colors may repeat and share exterior roles.')
INVARIANTS = [
    'rectangular integer grid with zero background and colors 0..9',
    'one to four complete monochrome four-connected yellow rectangular frames',
    'each frame is at least 4x4 with exactly one non-{0,4} interior marker cell',
    'frame boxes do not overlap or nest; exterior non-yellow objects may touch borders',
    'requested counts and total palette sizes are realized or explicitly rejected',
]
AXES = {
    'grid_h': {'type': 'int', 'default': 'canonical 12..14 or contrast 12..22', 'valid': '5..22'},
    'grid_w': {'type': 'int', 'default': 'canonical 11..13 or contrast 11..22', 'valid': '5..22'},
    'n_frames': {'type': 'int', 'default': 'canonical 1..3 or contrast 2..4', 'valid': '1..4'},
    'palette_size': {'type': 'int', 'default': 'total colors including 0 and 4; 4..10', 'valid': '3..10'},
    'n_distractors': {'type': 'int', 'default': '3..8 exterior nonzero cells', 'valid': '0..12'},
}
# Compatibility spelling, not another degree of freedom in the axis matrix.
OVERRIDE_ALIASES = {'n_distinct_colors': 'palette_size'}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
# Negative diagnostic fixtures are deliberately outside the lawful AXES domain.
DEGENERATE_TEXTURES = ('no_frames', 'no_marker', 'multiple_markers')
_MARKER_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
_CANONICAL_MARKERS = frozenset((1, 2, 3, 6, 8))
_PROFILES = ((14, 11, 5, 2, 5), (12, 11, 5, 1, 4), (12, 13, 4, 1, 3),
             (13, 11, 5, 2, 4), (14, 12, 6, 3, 5))
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ('canonical', 'contrast')
MIN_STRICT_FRAC = 1.0


class IncompatibleOverrides(ValueError):
    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def schedule_profile(seed, sample_index, difficulty=None):
    return 'contrast' if sample_index % 4 in (1, 2) else 'canonical'


def _integer(ctx, name, lo, hi, choices):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(choices))


def _separated(a, b):
    r, c, h, w = a
    ar, ac, ah, aw = b
    return r + h < ar or ar + ah < r or c + w < ac or ac + aw < c


def _place_frames(ctx, height, width, count, exterior, max_side):
    """Try varied locations, then use a guaranteed complete packing."""
    rng = ctx.draw_rng('frame_geometry')
    area_limit = height * width - exterior - 1
    for _ in range(6):
        boxes, used = [], 0
        for index in range(count):
            for _ in range(48):
                rh = rng.randint(4, min(max_side, height))
                rw = rng.randint(4, min(max_side, width))
                if used + rh * rw + 16 * (count - index - 1) > area_limit:
                    continue
                box = (rng.randint(0, height - rh), rng.randint(0, width - rw), rh, rw)
                if all(_separated(box, prior) for prior in boxes):
                    boxes.append(box)
                    used += rh * rw
                    break
            else:
                break
        if len(boxes) == count:
            return sorted(boxes)
    # Never return a partial placement. The caller checked this finite capacity.
    layouts = [(rows, (count + rows - 1) // rows) for rows in range(1, count + 1)
               if 5 * rows - 1 <= height
               and 5 * ((count + rows - 1) // rows) - 1 <= width]
    rows, cols = rng.choice(layouts)
    top = rng.randint(0, height - (5 * rows - 1))
    left = rng.randint(0, width - (5 * cols - 1))
    selected = rng.sample([(r, c) for r in range(rows) for c in range(cols)], count)
    return sorted((top + 5*r, left + 5*c, 4, 4) for r, c in selected)


def _put_exterior(grid, boxes, colors, rng):
    """Place every exterior cell, growing small objects as well as singletons."""
    free = {(r, c) for r in range(len(grid)) for c in range(len(grid[0]))
            if not any(br <= r < br+bh and bc <= c < bc+bw for br, bc, bh, bw in boxes)}
    if len(colors) > len(free) - 1:
        raise RuntimeError('constructive placement failed exterior capacity check')
    placed = []
    for color in colors:
        neighbors = sorted({(r+dr, c+dc) for r, c in placed
                            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                            if (r+dr, c+dc) in free})
        point = rng.choice(neighbors if neighbors and rng.random() < 0.65 else sorted(free))
        r, c = point
        grid[r][c] = color
        free.remove(point)
        placed.append(point)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError('seed must be an integer, not a boolean')
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError('sample_index must be a nonnegative integer')
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ('easy', 'medium', 'hard')):
        raise ValueError('difficulty must be None, easy, medium, or hard')

    def incompatible(message, axes):
        return IncompatibleOverrides(message, [name for name in axes if overrides.get(name) is not None])

    unknown = set(overrides) - set(AXES) - set(OVERRIDE_ALIASES) - {'texture'}
    if unknown:
        raise ValueError(f'unknown override axes: {sorted(unknown)}')
    if 'texture' in overrides:
        if overrides['texture'] not in DEGENERATE_TEXTURES:
            raise ValueError('texture only supports named negative diagnostic fixtures')
        if len(overrides) > 1:
            raise incompatible('negative fixtures do not accept normal axes', tuple(overrides))
        return _draw_from_degenerate(overrides['texture'], None)
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f'{name} must be an integer, not {type(value).__name__}')
    a, b = overrides.get('palette_size'), overrides.get('n_distinct_colors')
    if a is not None and b is not None and a != b:
        raise incompatible('palette aliases must agree', ('palette_size', 'n_distinct_colors'))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    contrast = schedule_profile(seed, sample_index, difficulty) == 'contrast'
    ph, pw, pk, pn, pd = ctx.draw_choice('canonical_profile', _PROFILES)
    upper = {'easy': 16, 'medium': 19, 'hard': 22}[difficulty or 'medium']
    height = _integer(ctx, 'grid_h', 5, 22, range(12, upper+1) if contrast else (ph,))
    width = _integer(ctx, 'grid_w', 5, 22, range(11, upper+1) if contrast else (pw,))
    capacity = min(4, ((height+1)//5) * ((width+1)//5))
    default_cap = min(capacity, 3 if difficulty == 'easy' else 4)
    preferred = range(min(2, default_cap), default_cap+1) if contrast else (min(pn, capacity),)
    count = _integer(ctx, 'n_frames', 1, 4, preferred)
    if count > capacity:
        raise incompatible('frames cannot fit with a one-cell separator',
                                    ('grid_h', 'grid_w', 'n_frames'))
    max_exterior = min(12, height*width - 16*count - 1)
    requested_palette = a if a is not None else b
    needed_exterior = max(0, (requested_palette or 3) - 2 - count)
    if needed_exterior > max_exterior:
        raise incompatible('palette cannot fit beside requested frames',
                                    ('grid_h', 'grid_w', 'n_frames', 'palette_size', 'n_distinct_colors'))
    defaults = (range(max(3, needed_exterior), max(3, needed_exterior, 8)+1)
                if contrast else (max(pd, needed_exterior),))
    choices = [n for n in defaults if n <= max_exterior] or (max_exterior,)
    exterior = _integer(ctx, 'n_distractors', 0, 12, choices)
    if exterior > max_exterior:
        raise incompatible('exterior cells cannot fit beside frames and background',
                                    ('grid_h', 'grid_w', 'n_frames', 'n_distractors'))
    palette_capacity = min(10, 2+count+exterior)
    if requested_palette is not None and not 3 <= requested_palette <= 10:
        raise ValueError('palette size must be in 3..10')
    if requested_palette is not None and requested_palette > palette_capacity:
        raise incompatible('palette requires more marker/exterior cells than requested',
                                    ('palette_size', 'n_distinct_colors', 'n_frames', 'n_distractors'))
    defaults = range(min(5, palette_capacity), palette_capacity+1) if contrast else (min(pk, palette_capacity),)
    target = requested_palette if requested_palette is not None else ctx.draw_choice('palette_target', tuple(defaults))
    palette_size = _integer(ctx, 'palette_size', 3, 10, (target,))
    _integer(ctx, 'n_distinct_colors', 3, 10, (palette_size,))
    color_rng = ctx.draw_rng('palette_roles')
    role_colors = color_rng.sample(_MARKER_COLORS, palette_size-2)
    rich = contrast and count >= 2 and palette_size >= 4
    if rich and not any(c not in _CANONICAL_MARKERS for c in role_colors):
        role_colors[0] = color_rng.choice((5, 7, 9))
    color_rng.shuffle(role_colors)
    minimum_unique = max(1, len(role_colors)-exterior, 2 if rich else 1)
    unique_count = color_rng.randint(minimum_unique, min(count, len(role_colors)))
    marker_palette = color_rng.sample(role_colors, unique_count)
    if rich and not any(c not in _CANONICAL_MARKERS for c in marker_palette):
        marker_palette[0] = color_rng.choice([c for c in role_colors if c not in _CANONICAL_MARKERS])
    marker_colors = marker_palette + [color_rng.choice(marker_palette) for _ in range(count-unique_count)]
    color_rng.shuffle(marker_colors)
    missing = [c for c in role_colors if c not in marker_colors]
    exterior_colors = missing + [color_rng.choice(role_colors) for _ in range(exterior-len(missing))]
    color_rng.shuffle(exterior_colors)
    boxes = _place_frames(ctx, height, width, count, exterior, 7 if contrast and difficulty != 'easy' else 6)
    grid = full_grid(height, width, 0)
    marker_rng = ctx.draw_rng('interior_positions')
    for (r, c, rh, rw), color in zip(boxes, marker_colors):
        draw_rect_outline(grid, r, c, rh, rw, 4)
        grid[marker_rng.randint(r+1, r+rh-2)][marker_rng.randint(c+1, c+rw-2)] = color
    _put_exterior(grid, boxes, exterior_colors, ctx.draw_rng('exterior_positions'))
    return grid


def _analyze(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError('expected a nonempty list-of-lists grid')
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError('grid must be rectangular and at most 30x30')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('grid colors must be integers 0..9, not booleans')
    if not any(v == 0 for row in grid for v in row):
        raise ValueError('zero background is required')
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4}
    frames = []
    while pending:
        start = min(pending)
        pending.remove(start)
        component, frontier = {start}, [start]
        while frontier:
            r, c = frontier.pop()
            for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if point in pending:
                    pending.remove(point)
                    component.add(point)
                    frontier.append(point)
        top, bottom = min(r for r, _ in component), max(r for r, _ in component)
        left, right = min(c for _, c in component), max(c for _, c in component)
        if bottom-top < 3 or right-left < 3:
            raise ValueError('each yellow frame must be at least 4x4')
        perimeter = {(r, c) for r in range(top, bottom+1) for c in range(left, right+1)
                     if r in (top, bottom) or c in (left, right)}
        if component != perimeter:
            raise ValueError('yellow component is not a complete hollow rectangular perimeter')
        inside = [(r, c) for r in range(top+1, bottom) for c in range(left+1, right) if grid[r][c] != 0]
        if len(inside) != 1 or grid[inside[0][0]][inside[0][1]] == 4:
            raise ValueError('each frame interior needs exactly one non-yellow marker cell')
        mr, mc = inside[0]
        frames.append((top, left, bottom, right, grid[mr][mc]))
    if not 1 <= len(frames) <= 4:
        raise ValueError('expected one to four yellow frames')
    for i, (r, c, b, d, _) in enumerate(frames):
        if any(not (b < ar or ab < r or d < ac or ad < c) for ar, ac, ab, ad, _ in frames[i+1:]):
            raise ValueError('frame boxes must not overlap or nest')
    return frames


def observe_overrides(grid):
    frames = _analyze(grid)
    exterior = sum(v != 0 and not any(t <= r <= b and l <= c <= rr for t, l, b, rr, _ in frames)
                   for r, row in enumerate(grid) for c, v in enumerate(row))
    palette = len({v for row in grid for v in row})
    return {'grid_h': len(grid), 'grid_w': len(grid[0]), 'n_frames': len(frames),
            'palette_size': palette, 'n_distinct_colors': palette, 'n_distractors': exterior}


def self_check(grid, *, difficulty=None, meta=None):
    try:
        observed = observe_overrides(grid)
    except (ValueError, TypeError, IndexError) as exc:
        return [str(exc)]
    expected = meta or {}
    if isinstance(expected.get('overrides'), dict):
        expected = expected['overrides']
    return [f'{name}: requested {expected[name]}, observed {value}'
            for name, value in observed.items() if expected.get(name) is not None and expected[name] != value]


def strict_canonical_like(grid):
    """Lawful frame/marker manifold; exact size/palette is checked separately."""
    return self_check(grid)


def _draw_from_degenerate(name, rng):
    grid = full_grid(11, 12, 0)
    if name == 'no_frames':
        grid[2][3], grid[5][8] = 3, 6
        return grid
    draw_rect_outline(grid, 2, 2, 5, 6, 4)
    if name == 'multiple_markers':
        grid[3][3], grid[5][6] = 3, 6
    return grid


def _rival(grid, mode):
    """Competing hypotheses only; never called to generate labels."""
    frames = _analyze(grid)
    out = [row[:] for row in grid]
    if mode == 'identity':
        return out
    for index, (top, left, bottom, right, marker) in enumerate(frames):
        if mode == 'first_frame' and index:
            continue
        if mode == 'canonical_marker_palette' and marker not in _CANONICAL_MARKERS:
            continue
        color = frames[0][4] if mode == 'global_marker' else marker
        for r in range(top, bottom+1):
            for c in range(left, right+1):
                interior = top < r < bottom and left < c < right
                if (interior and grid[r][c] == 0) or (mode == 'paint_border' and not interior):
                    out[r][c] = color
    if mode == 'erase_exterior':
        for r, row in enumerate(out):
            for c in range(len(row)):
                if not any(t <= r <= b and l <= c <= rr for t, l, b, rr, _ in frames):
                    out[r][c] = 0
    return out


def _identity(grid):
    return _rival(grid, 'identity')


def _erase_exterior(grid):
    return _rival(grid, 'erase_exterior')


def _first_frame(grid):
    return _rival(grid, 'first_frame')


def _global_marker(grid):
    return _rival(grid, 'global_marker')


def _paint_border(grid):
    return _rival(grid, 'paint_border')


def _canonical_marker_palette(grid):
    return _rival(grid, 'canonical_marker_palette')


SEMANTIC_RIVALS = {'identity': _identity, 'erase_exterior': _erase_exterior,
                   'first_frame_only': _first_frame, 'global_marker': _global_marker,
                   'paint_border': _paint_border, 'canonical_marker_palette': _canonical_marker_palette}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {'canonical_marker_palette': _canonical_marker_palette}
SEMANTIC_WITNESSES = {
    'exterior_preservation': lambda g: observe_overrides(g)['n_distractors'] > 0,
    'multiple_frames': lambda g: len(_analyze(g)) > 1,
    'different_markers': lambda g: len({frame[4] for frame in _analyze(g)}) > 1,
    'novel_marker_role': lambda g: any(frame[4] not in _CANONICAL_MARKERS for frame in _analyze(g)),
}
WITNESS_RIVALS = {'exterior_preservation': ['erase_exterior'], 'multiple_frames': ['first_frame_only'],
                  'different_markers': ['global_marker'], 'novel_marker_role': ['canonical_marker_palette']}


def lesson_identifiable(demos, query):
    return [f'{name} fits every demonstration but changes the query'
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair['input']) == pair['output'] for pair in demos)
            and rival(query['input']) != query['output']]
