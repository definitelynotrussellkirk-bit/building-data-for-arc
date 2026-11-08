"""Safe path concatenation inputs for canonical ARC task d017b73f.

Construct the packed paths first, inside the retained-height canvas; then
separate their column bands and randomize later paths' input rows. Labels are
still executed by the existing Racket authority, never generated here.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = '664a918eb273'
TASK_ID = GENERATOR_ID
VERSION = '4.0.0'
RULE_HASH = '0bf6f91bb8f8'
SUMMARY = (
    'Join separated monochrome paths in left-to-right order, preserving the '
    'first path position. Align each later entry one cell right of the previous '
    'exit, preserve input height, and trim the right edge. Safe constructive '
    'sampling mixes 3-row canonical-like scenes with 4..12-row extensions, '
    '2..5 paths, repeated colors, longer shapes, and variable left margins.'
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    'zero background; at least two separated monochrome eight-connected components',
    'every component is a simple four-neighbor path with exactly two endpoints',
    'the unique leftmost cell is its entry endpoint and the other endpoint is rightmost',
    'packing preserves every colored cell without overlap or vertical clipping',
    'objects are ordered by disjoint column bands, not by their colors',
]
AXES = {
    'grid_h': {'type': 'int', 'default': 'core 3; expanded 4..12', 'valid': '3..12'},
    'grid_w': {'type': 'int', 'default': 'core 9..11; expanded 14..30', 'valid': '8..30'},
    'n_paths': {'type': 'int', 'default': 'core 3..4; expanded 2..5', 'valid': '2..5'},
    'n_distinct_colors': {'type': 'int', 'default': '1..n_paths', 'valid': '1..5'},
    'gap': {'type': 'int', 'default': 'core 1; expanded 1..3', 'valid': '1..3'},
    'anchor_col': {'type': 'int', 'default': 'core 0; expanded 1..3', 'valid': '0..3'},
}
_LIMITS = {'grid_h': (3, 12), 'grid_w': (8, 30), 'n_paths': (2, 5),
           'n_distinct_colors': (1, 5), 'gap': (1, 3), 'anchor_col': (0, 3)}
# A nonempty declaration enables the strict checker. Exceptions below also
# identify the actual conflicting axes rather than silently dropping paths.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ('grid_w', 'n_paths'), ('grid_w', 'gap'), ('grid_w', 'anchor_col'),
    ('n_paths', 'n_distinct_colors'), ('grid_w', 'n_distinct_colors'),
]
MIN_STRICT_FRAC = 0.4
_D4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_D8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)


class IncompatibleLayout(ValueError):
    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def _draw_int(ctx, name, lo, hi):
    # Explicit overrides use the public domain, not a difficulty sub-band.
    if name in ctx.overrides:
        return ctx.draw_int(name, *_LIMITS[name])
    return ctx.draw_int(name, lo, hi)


def _components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    result = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        cells, stack = {first}, [first]
        while stack:
            r, c = stack.pop()
            for dr, dc in _D8:
                other = r + dr, c + dc
                if other in unseen:
                    unseen.remove(other)
                    cells.add(other)
                    stack.append(other)
        result.append(cells)
    return sorted(result, key=lambda cells: min(c for _, c in cells))


def _analyze(grid):
    """Geometry validation only: no reference invocation or label admission."""
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ['empty or malformed grid'], [], []
    h, w = len(grid), len(grid[0])
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return ['grid dimensions must lie in 1..30'], [], []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ['ragged grid'], [], []
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ['grid colors must be integer ARC colors 0..9'], [], []
    parts = _components(grid)
    errors, infos, shifted = [], [], []
    if len(parts) < 2:
        errors.append('need at least two separated paths for this lesson')
    previous, occupied, last_right = None, set(), -1
    for cells in parts:
        left, right = min(c for _, c in cells), max(c for _, c in cells)
        if left <= last_right:
            errors.append('component column bands overlap')
        last_right = right
        colors = {grid[r][c] for r, c in cells}
        if len(colors) != 1:
            errors.append('component is not monochrome')
        deg = {p: sum((p[0] + dr, p[1] + dc) in cells for dr, dc in _D4) for p in cells}
        endpoints = [p for p in sorted(cells) if deg[p] == 1]
        entry = min(cells, key=lambda p: (p[1], p[0]))
        # Degrees alone do not prove four-connectivity after eight-connected
        # extraction (a diagonal cycle plus a line is a counterexample).
        todo, reached = [entry], {entry}
        while todo:
            r, c = todo.pop()
            for dr, dc in _D4:
                p = r + dr, c + dc
                if p in cells and p not in reached:
                    reached.add(p)
                    todo.append(p)
        if reached != cells or len(endpoints) != 2 or any(d not in (1, 2) for d in deg.values()):
            errors.append('component is not a simple orthogonal path')
            continue
        if entry not in endpoints or sum(c == left for r, c in cells) != 1:
            errors.append('entry must be the unique leftmost endpoint')
            continue
        exit_cell = next(p for p in endpoints if p != entry)
        if exit_cell[1] != right:
            errors.append('exit is not on the rightmost column')
            continue
        dr, dc = (0, 0) if previous is None else (previous[0] - entry[0], previous[1] + 1 - entry[1])
        placed = {(r + dr, c + dc) for r, c in cells}
        if any(r < 0 or r >= h or c < 0 for r, c in placed):
            errors.append('packing would clip a colored cell')
        if placed & occupied:
            errors.append('packing would overwrite a colored cell')
        occupied.update(placed)
        color = grid[entry[0]][entry[1]]
        infos.append({'cells': cells, 'entry': entry, 'exit': exit_cell,
                      'color': color, 'dr': dr, 'dc': dc})
        shifted.append((placed, color))
        previous = exit_cell[0] + dr, exit_cell[1] + dc
    return sorted(set(errors)), infos, shifted


def self_check(grid, *, difficulty=None, meta=None):
    return _analyze(grid)[0]


def _grow_path(rng, h, entry_row, max_width, target_length):
    """Monotone-column, induced orthogonal walk; left entry stays unique.

    An east step is forced first. Each subsequent cell touches only the current
    endpoint, preventing forks, loops, and filled 2x2 squares. All packed rows
    stay in bounds from construction, not by clipping or rejection afterward.
    """
    cells = [(entry_row, 0), (entry_row, 1)]
    seen = set(cells)
    while len(cells) < target_length:
        r, c = cells[-1]
        candidates = []
        for dr, dc in ((0, 1), (-1, 0), (1, 0)):
            p = r + dr, c + dc
            if not (0 <= p[0] < h and p[1] < max_width) or p in seen:
                continue
            if sum((p[0] + a, p[1] + b) in seen for a, b in _D4) == 1:
                candidates.append(p)
        if not candidates:
            break
        p = rng.choice(candidates)
        cells.append(p)
        seen.add(p)
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f'unknown override axes: {sorted(unknown)}')
    for name, value in overrides.items():
        lo, hi = _LIMITS[name]
        if type(value) is not int:
            raise TypeError(f'{name} must be an integer, not {type(value).__name__}')
        if not lo <= value <= hi:
            raise ValueError(f'{name} must lie in {lo}..{hi}')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('difficulty must be easy, medium, hard, or None')
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = sample_index % 2 == 0
    rng = ctx.draw_rng('layout')
    palette_rng = ctx.draw_rng('palette_assignment')
    h = _draw_int(ctx, 'grid_h', 3 if core else 4, 3 if core else 12)
    budget = overrides.get('grid_w', 30)
    min_gap, min_anchor = overrides.get('gap', 1), overrides.get('anchor_col', 0)
    max_count = min(5, (budget - min_anchor + min_gap) // (2 + min_gap))
    required_colors = overrides.get('n_distinct_colors', 1)
    if max_count < max(2, required_colors):
        raise IncompatibleLayout('width cannot fit the requested colors and separated paths',
                                 ('grid_w', 'n_distinct_colors', 'gap', 'anchor_col'))
    n_lo = max(required_colors, min(3 if core else 2, max_count))
    n_hi = min(max_count, max(4 if core else 5, required_colors))
    n = _draw_int(ctx, 'n_paths', n_lo, n_hi)
    if n > max_count:
        raise IncompatibleLayout('width cannot fit the requested number of paths',
                                 ('grid_w', 'n_paths', 'gap', 'anchor_col'))
    if required_colors > n:
        raise IncompatibleLayout('distinct colors cannot exceed path count',
                                 ('n_paths', 'n_distinct_colors'))
    k = _draw_int(ctx, 'n_distinct_colors', 1, n)
    gap_hi = min(3, (budget - min_anchor - 2 * n) // (n - 1))
    gap = _draw_int(ctx, 'gap', 1, 1 if core else gap_hi)
    anchor_hi = min(3, budget - 2 * n - (n - 1) * gap)
    if anchor_hi < 0:
        raise IncompatibleLayout('width cannot fit the requested inter-path gap',
                                 ('grid_w', 'n_paths', 'gap'))
    anchor = _draw_int(ctx, 'anchor_col', 0 if core else min(1, anchor_hi), 0 if core else anchor_hi)
    minimum_width = anchor + 2 * n + (n - 1) * gap
    if minimum_width > budget:
        raise IncompatibleLayout('width cannot fit the requested anchor and paths',
                                 ('grid_w', 'n_paths', 'gap', 'anchor_col'))
    default_lo = max(minimum_width, 9 if core else 14)
    w = _draw_int(ctx, 'grid_w', default_lo, max(default_lo, 11 if core else 30))
    palette = ctx.draw_distinct_colors('colors', n=k, exclude={0})
    colors = list(palette) + [palette_rng.choice(palette) for _ in range(n - k)]
    palette_rng.shuffle(colors)
    g = full_grid(h, w, 0)
    column, packed_row = anchor, rng.randrange(h)
    available_width = w - anchor - (n - 1) * gap
    max_length = 4 if core else {'easy': 5, 'medium': 8, 'hard': 11, None: 9}[difficulty]
    for index, color in enumerate(colors):
        remaining = n - index - 1
        max_width = min(5, available_width - 2 * remaining)
        path = _grow_path(rng, h, packed_row, max_width, rng.randint(2, max_length))
        lo_row, hi_row = min(r for r, _ in path), max(r for r, _ in path)
        width = max(c for _, c in path) + 1
        # Keep first path exactly fixed. Other input rows are independent of
        # the safe packed-row construction and need the endpoint alignment.
        offset = 0 if index == 0 else rng.randint(0, h - (hi_row - lo_row + 1)) - lo_row
        for r, c in path:
            g[r + offset][column + c] = color
        packed_row = path[-1][0]
        column += width + gap
        available_width -= width
    return g


def observe_overrides(grid):
    errors, infos, _ = _analyze(grid)
    if errors:
        raise ValueError('; '.join(errors))
    gaps = [min(c for r, c in b['cells']) - max(c for r, c in a['cells']) - 1
            for a, b in zip(infos, infos[1:])]
    return {'grid_h': len(grid), 'grid_w': len(grid[0]), 'n_paths': len(infos),
            'n_distinct_colors': len({item['color'] for item in infos}),
            'gap': gaps[0] if len(set(gaps)) == 1 else None,
            'anchor_col': infos[0]['entry'][1]}


def strict_canonical_like(grid):
    errors, infos, _ = _analyze(grid)
    if errors:
        return errors
    if (len(grid) != 3 or not 9 <= len(grid[0]) <= 11 or not 3 <= len(infos) <= 4
            or infos[0]['entry'][1] != 0 or any(len(info['cells']) > 4 for info in infos)):
        return ['not a small three-row, three/four-path canonical-style scene']
    return []


def _has_anchor(grid):
    errors, infos, _ = _analyze(grid)
    return not errors and infos[0]['entry'][1] > 0


def _has_repeated_color(grid):
    errors, infos, _ = _analyze(grid)
    return not errors and len({info['color'] for info in infos}) < len(infos)


def _needs_vertical_alignment(grid):
    errors, infos, _ = _analyze(grid)
    return not errors and any(info['dr'] != 0 for info in infos)


SEMANTIC_WITNESSES = {
    'nonzero_anchor_refutes_left_justify': _has_anchor,
    'repeated_colors_require_components_not_color_groups': _has_repeated_color,
    'vertical_alignment_not_just_empty_column_deletion': _needs_vertical_alignment,
}


def _rival_render(grid, *, left_justify=False, omit_repeats=False, horizontal_only=False):
    """Executable competitors for review gates, NEVER a training-label source.

    The named switches intentionally change the rule. The Racket semantic gate
    checks actual disagreement; a feature being present alone is not evidence.
    """
    errors, infos, _ = _analyze(grid)
    if errors:
        return None
    colored, seen_colors, previous = [], set(), None
    anchor = infos[0]['entry'][1] if left_justify else 0
    for info in infos:
        if omit_repeats and info['color'] in seen_colors:
            continue
        seen_colors.add(info['color'])
        if previous is None:
            dr, dc = 0, -anchor
        else:
            dr = 0 if horizontal_only else previous[0] - info['entry'][0]
            dc = previous[1] + 1 - info['entry'][1]
        colored.extend((r + dr, c + dc, info['color']) for r, c in info['cells'])
        previous = info['exit'][0] + dr, info['exit'][1] + dc
    width = max(c for r, c, color in colored) + 1
    output = full_grid(len(grid), width, 0)
    for r, c, color in colored:
        if 0 <= r < len(grid) and 0 <= c < width:
            output[r][c] = color
    return output


def _left_justify(grid):
    return _rival_render(grid, left_justify=True)


def _one_path_per_color(grid):
    return _rival_render(grid, omit_repeats=True)


def _horizontal_pack_only(grid):
    return _rival_render(grid, horizontal_only=True)


SEMANTIC_RIVALS = {
    'left_justify_packed_chain': _left_justify,
    'keep_only_first_path_of_each_color': _one_path_per_color,
    'pack_columns_without_vertical_alignment': _horizontal_pack_only,
}
WITNESS_RIVALS = {
    'nonzero_anchor_refutes_left_justify': ['left_justify_packed_chain'],
    'repeated_colors_require_components_not_color_groups': ['keep_only_first_path_of_each_color'],
    'vertical_alignment_not_just_empty_column_deletion': ['pack_columns_without_vertical_alignment'],
}
CANONICAL_SHORTCUTS = {'left_justify_packed_chain': _left_justify}
SCHEDULE_PROFILES = ('canonical_like', 'expanded')


def schedule_profile(seed, sample_index, difficulty=None):
    """Observed for default draws; explicit overrides may leave the core profile."""
    return SCHEDULE_PROFILES[sample_index % 2]
