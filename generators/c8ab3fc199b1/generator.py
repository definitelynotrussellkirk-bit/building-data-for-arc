"""Source-preserving generator for top-marker / bottom-docked crop puzzles.

Every top marker has exactly one same-color 4-connected component in the
remaining rows. The selected Racket rule crops each component to its bbox and
bottom-aligns that crop at the marker's column. Shapes, source locations,
marker docks, area, height, colors, and object count are varied independently.
Unmarked body colors can also appear as distractors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = 'c8ab3fc199b1'
VERSION = '1.2.0'
SUMMARY = 'Variable same-colored blobs docked beneath matching top-row marker cells.'
INVARIANTS = [
    'Row zero has 2..4 distinct nonzero marker colors.',
    'Each marker color occurs in exactly one 4-connected body component.',
    'Every selected crop fits in its marker column without output overlap.',
    'Body object shapes, marker columns and color associations vary by draw.',
]
PALETTE_KINDS = ('default', 'warm', 'cool', 'varied')
DEGENERATE_TEXTURES = ('no_markers', 'marker_without_body', 'body_without_marker')
AXES = {
    'grid_h': {'type': 'int', 'default': 'difficulty-dependent 6..14', 'valid': '6..14'},
    'grid_w': {'type': 'int', 'default': 'difficulty-dependent 10..16', 'valid': '10..16'},
    'n_markers': {'type': 'int', 'default': 'rng 2..4, centered on 3', 'valid': '2..4'},
    'n_distinct_colors': {'type': 'int', 'default': 'equals n_markers', 'valid': '2..4'},
    'palette_size': {'type': 'int', 'default': 'equals n_markers', 'valid': '2..4'},
    'palette_kind': {'type': 'str', 'default': 'rng palette_kind',
                     'valid': '|'.join(PALETTE_KINDS)},
    'position_bias': {'type': 'str', 'default': 'separated_docks_permuted_sources',
                      'valid': 'separated_docks_permuted_sources'},
    'density': {'type': 'str', 'default': 'sparse', 'valid': 'sparse|medium'},
    'texture': {'type': 'str', 'default': 'alias for palette_kind',
                'valid': '|'.join(PALETTE_KINDS + DEGENERATE_TEXTURES)},
}


def _polyomino(height, width, target, rng):
    cells = {(r, 0) for r in range(height)} | {(0, c) for c in range(width)}
    while len(cells) < target:
        rim = {(r + dr, c + dc) for r, c in cells
               for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if 0 <= r + dr < height and 0 <= c + dc < width
               and (r + dr, c + dc) not in cells}
        cells.add(rng.choice(sorted(rim)))
    if rng.randrange(2):
        cells = {(height - 1 - r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, width - 1 - c) for r, c in cells}
    return sorted(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if difficulty == 'easy':
        h = ctx.draw_int_strict('grid_h', 6, 9)
        w = ctx.draw_int_strict('grid_w', 10, 13)
    elif difficulty == 'hard':
        h = ctx.draw_int_strict('grid_h', 10, 14)
        w = ctx.draw_int_strict('grid_w', 13, 16)
    else:
        h = ctx.draw_int_strict('grid_h', 6, 14)
        w = ctx.draw_int_strict('grid_w', 10, 16)

    layout = ctx.draw_rng('layout')
    declared_count = [overrides[k] for k in
                      ('n_markers', 'n_distinct_colors', 'palette_size')
                      if overrides.get(k) is not None]
    if any(type(v) is not int or not 2 <= v <= 4 for v in declared_count):
        raise ValueError('Marker/color count overrides must be exact integers 2..4')
    if len(set(declared_count)) > 1:
        raise ValueError('n_markers, n_distinct_colors, palette_size must agree')
    n = declared_count[0] if declared_count else layout.choice([2, 3, 3, 3, 4])
    # Exact draw bounds make these relational axes reject contradictory overrides.
    ctx.draw_int_strict('n_markers', n, n)
    ctx.draw_int_strict('n_distinct_colors', n, n)
    ctx.draw_int_strict('palette_size', n, n)
    ctx.draw_choice('position_bias', ('separated_docks_permuted_sources',))
    density = ctx.draw_choice('density', ('sparse', 'medium'))

    texture_override = overrides.get('texture')
    if texture_override is not None:
        if type(texture_override) is not str or texture_override not in (
                PALETTE_KINDS + DEGENERATE_TEXTURES):
            raise ValueError('Unrecognized texture override')
        if texture_override in DEGENERATE_TEXTURES:
            ctx.draw_choice('texture', (texture_override,))
            return _draw_from_degenerate(texture_override)
        if overrides.get('palette_kind') not in (None, texture_override):
            raise ValueError('texture and palette_kind aliases must agree')
        palette_kind = ctx.draw_choice('palette_kind', (texture_override,))
        ctx.draw_choice('texture', (texture_override,))
    else:
        palette_kind = ctx.draw_choice('palette_kind', PALETTE_KINDS)

    palette_options = {
        'default': [2, 3, 4, 6, 7, 8, 9, 5],
        'warm': [1, 2, 3, 4, 5, 6],
        'cool': [4, 5, 6, 7, 8, 9],
        'varied': list(range(1, 10)),
    }[palette_kind]
    colors = layout.sample(palette_options, n)
    grid = full_grid(h, w, 0)
    starts = [i * w // n for i in range(n)]
    ends = [(i + 1) * w // n - 1 for i in range(n)]
    min_section = min(b - a + 1 for a, b in zip(starts, ends))
    max_w = min(4, min_section)
    max_h = min(6, h - 2)
    shapes = []
    for _ in range(n):
        sh = layout.randint(2, max_h)
        sw = layout.randint(1, max_w)
        area_min = sh + sw - 1
        frac = layout.uniform(0.45, 0.90) if density == 'sparse' else layout.uniform(0.65, 1.0)
        area = min(sh * sw, max(area_min, int(sh * sw * frac)))
        shapes.append((sh, sw, _polyomino(sh, sw, area, layout)))
    # Source column, dock column, and marker color are independently shuffled.
    max_crop_width = max(sw for sh, sw, cells in shapes)
    dock_cols = [layout.randint(a, b - max_crop_width + 1)
                 for a, b in zip(starts, ends)]
    for anchor, color in zip(dock_cols, colors):
        grid[0][anchor] = color
    strips = list(range(n)); layout.shuffle(strips)
    order = list(range(n)); layout.shuffle(order)
    for marker_index, shape_index in enumerate(order):
        sh, sw, cells = shapes[shape_index]
        s = strips[marker_index]
        x = layout.randint(starts[s], ends[s] - sw + 1)
        y = layout.randint(2, h - sh)
        for dr, dc in cells:
            assert grid[y + dr][x + dc] == 0
            grid[y + dr][x + dc] = colors[marker_index]
    return grid


def _draw_from_degenerate(name):
    grid = full_grid(8, 13, 0)
    if name == 'no_markers':
        grid[2][1] = 2; grid[3][1] = 2
    elif name == 'marker_without_body':
        grid[0][1] = 2; grid[0][6] = 5
        grid[2][1] = 2; grid[3][1] = 2
    elif name == 'body_without_marker':
        grid[0][1] = 2; grid[0][6] = 5
        grid[2][1] = 2; grid[3][1] = 2
        grid[2][6] = 5; grid[3][6] = 5
        grid[3][11] = 6; grid[4][11] = 6
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Guard the single-component, unique-color, fit and no-collision grammar."""
    bad = []
    if (type(grid) is not list or not 2 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        return ['invalid grid dimensions']
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w
           or any(type(v) is not int or not 0 <= v <= 9 for v in row)
           for row in grid):
        return ['grid must contain exact ARC integers in rectangular rows']
    markers = [(c, col) for c, col in enumerate(grid[0]) if col]
    if not 2 <= len(markers) <= 4 or len({col for _, col in markers}) != len(markers):
        bad.append('expected 2..4 uniquely-colored top-row markers')
    crops = []
    for marker_col, color in markers:
        cells = {(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == color}
        if not cells:
            bad.append(f'body lacks color {color}')
            continue
        rem = set(cells); frontier = [next(iter(cells))]
        while frontier:
            r, c = frontier.pop()
            if (r, c) not in rem:
                continue
            rem.remove((r, c))
            frontier.extend((r + dr, c + dc) for dr, dc in
                            ((-1, 0), (1, 0), (0, -1), (0, 1))
                            if (r + dr, c + dc) in rem)
        if rem:
            bad.append(f'multiple components of color {color}')
        width = max(c for r, c in cells) - min(c for r, c in cells) + 1
        if marker_col + width > w:
            bad.append(f'crop of color {color} extends off right edge')
        else:
            crops.append((marker_col, marker_col + width))
    for i, (start, end) in enumerate(crops):
        if any(not (end <= a or b <= start) for a, b in crops[i + 1:]):
            bad.append('docked crops overlap in output')
            break
    return bad
