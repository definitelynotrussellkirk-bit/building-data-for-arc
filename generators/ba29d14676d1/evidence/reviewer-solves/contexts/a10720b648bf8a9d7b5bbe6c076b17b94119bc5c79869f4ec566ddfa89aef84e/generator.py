"""Input-only sampler for local left-right reflection in a color-9 lattice.

Canonical 3x11 inputs remain a recurring profile. Two counterexample profiles
per six consecutive draws teach variable tile width, every tile row/column,
and foreground-color independence. A third, independent profile decouples
those features. Labels always come from the unchanged Racket authority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.lattice import assemble_tiles, blank_tile

GENERATOR_ID = 'ba29d14676d1'
TASK_ID = GENERATOR_ID
RULE_HASH = '93b766a34b8e'
VERSION = '3.0.2'
SUMMARY = (
    'Mirror each equal-sized tile left-right in place, preserving the color-9 '
    'divider lattice. One foreground color on background 0; 1..3 tile rows, '
    '2..5 tile columns, tile height/width 2..5. Canonical 1x3, 3x3-tile '
    'examples alternate with shortcut witnesses and independent broad draws.'
)
INVARIANTS = [
    'regular equal-sized tiles with one-cell internal divider rows/columns of color 9',
    'tile cells contain 0 and exactly one foreground color in 1..8; no stray divider cells',
    'every tile is nonempty; at least one tile is left-right asymmetric',
    'all grids fit within 17 rows and 29 columns',
]
AXES = {
    'tile_rows': {'type': 'int', 'default': 'profile: 1, 2, or 1..3', 'valid': '1..3'},
    'tile_cols': {'type': 'int', 'default': 'profile: 3, 4, or 2..5', 'valid': '2..5'},
    'tile_h': {'type': 'int', 'default': 'profile: 3, 2..3, or 2..5', 'valid': '2..5'},
    'tile_w': {'type': 'int', 'default': 'profile: 3, 4..5, or 2..5', 'valid': '2..5'},
    'foreground': {'type': 'int', 'default': '1..8 (witness profile excludes 4)', 'valid': '1..8'},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.25
SCHEDULE_PROFILES = ('canonical', 'witness', 'independent')
DEGENERATE_TEXTURES = ('empty_tiles', 'lr_symmetric_tiles', 'no_tiles')


def schedule_profile(seed, sample_index, difficulty=None):
    """Every six consecutive accepted draws contain two of each profile."""
    return SCHEDULE_PROFILES[sample_index % 3]


def _axis(ctx, name, lo, hi, preferred):
    # Default profile restrictions are not override restrictions. Each exact
    # control has its full declared domain in every band and schedule position.
    options = tuple(range(lo, hi + 1)) if ctx.overrides.get(name) is not None else tuple(preferred)
    return ctx.draw_choice(name, options)


def _edge_asymmetric(tile):
    return any(row[0] != row[-1] for row in tile)


def _ensure_edge_asymmetry(tile, rng, fg):
    if not _edge_asymmetric(tile):
        row = tile[rng.randrange(len(tile))]
        row[0], row[-1] = rng.choice(((fg, 0), (0, fg)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f'unknown override axes: {sorted(unknown)}')
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f'{name} must be an integer, not {type(value).__name__}')
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    core, witness = profile == 'canonical', profile == 'witness'
    rows = _axis(ctx, 'tile_rows', 1, 3, (1,) if core else ((2,) if witness else (1, 2, 3)))
    cols = _axis(ctx, 'tile_cols', 2, 5, (3,) if core else ((4,) if witness else (2, 3, 4, 5)))
    th = _axis(ctx, 'tile_h', 2, 5, (3,) if core else ((2, 3) if witness else (2, 3, 4, 5)))
    tw = _axis(ctx, 'tile_w', 2, 5, (3,) if core else ((4, 5) if witness else (2, 3, 4, 5)))
    fg = _axis(ctx, 'foreground', 1, 8, (1, 2, 3, 5, 6, 7, 8) if witness else range(1, 9))
    cells = [(r, c) for r in range(th) for c in range(tw)]
    tiles = []
    for tr in range(rows):
        tile_row = []
        for tc in range(cols):
            rng = ctx.draw_rng(f'tile_{tr}_{tc}')
            tile = blank_tile(th, tw)
            # Retain the canonical 3..5 marks at 3x3, scale gently elsewhere.
            low = max(1, (th * tw + 3) // 4)
            high = min(th * tw - 1, max(low, (3 * th * tw) // 5))
            if difficulty == 'easy' and not core:
                high = max(low, (low + high + 1) // 2)
            for r, c in rng.sample(cells, rng.randint(low, high)):
                tile[r][c] = fg
            tile_row.append(tile)
        tiles.append(tile_row)
    # Random witness positions, not one marked corner. Symmetric individual
    # tiles remain possible, including in canonical-size grids. Each tile
    # row and each extra column (beyond the canonical three) has a witness.
    rng = ctx.draw_rng('witness_placement')
    for tile_row in tiles:
        if not any(_edge_asymmetric(t) for t in tile_row):
            _ensure_edge_asymmetry(rng.choice(tile_row), rng, fg)
    for tc in range(3, cols):
        if not any(_edge_asymmetric(tiles[tr][tc]) for tr in range(rows)):
            _ensure_edge_asymmetry(tiles[rng.randrange(rows)][tc], rng, fg)
    # A wider tile must teach reflection of the interior too, not merely
    # exchanging its outside columns. Do not alter the caller's tile width.
    if witness and tw >= 4 and not any(row[1] != row[-2]
                                      for tile_row in tiles for tile in tile_row for row in tile):
        row = rng.choice(rng.choice(rng.choice(tiles)))
        row[1], row[-2] = rng.choice(((fg, 0), (0, fg)))
    return assemble_tiles(tiles)


def _layout(grid):
    """Validate divider geometry; return row/column spans and foreground."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError('grid must be nonempty and rectangular')
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError('grid must be nonempty and rectangular')
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError('grid must be rectangular')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('cells must be integer colors 0..9, not booleans')
    sr = [r for r, row in enumerate(grid) if all(v == 9 for v in row)]
    sc = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    def spans(n, dividers):
        cuts = [-1] + dividers + [n]
        if any(b - a <= 1 for a, b in zip(cuts, cuts[1:])):
            raise ValueError('dividers must be internal, one cell wide, and separated by tiles')
        return [(a + 1, b) for a, b in zip(cuts, cuts[1:])]
    rs, cs = spans(h, sr), spans(w, sc)
    if len({b - a for a, b in rs}) != 1 or len({b - a for a, b in cs}) != 1:
        raise ValueError('all tiles must have equal height and equal width')
    if any(v == 9 and r not in sr and c not in sc for r, row in enumerate(grid) for c, v in enumerate(row)):
        raise ValueError('stray divider color 9 inside a tile')
    colors = {v for row in grid for v in row} - {0, 9}
    if len(colors) != 1:
        raise ValueError('expected exactly one foreground color in 1..8')
    return rs, cs, next(iter(colors))


def observe_overrides(grid):
    rs, cs, fg = _layout(grid)
    return dict(tile_rows=len(rs), tile_cols=len(cs), tile_h=rs[0][1] - rs[0][0],
                tile_w=cs[0][1] - cs[0][0], foreground=fg)


def self_check(grid, *, difficulty=None, meta=None):
    try:
        rs, cs, fg = _layout(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    th, tw = rs[0][1] - rs[0][0], cs[0][1] - cs[0][0]
    if not (1 <= len(rs) <= 3 and 2 <= len(cs) <= 5 and 2 <= th <= 5 and 2 <= tw <= 5):
        errors.append('expected 1..3 by 2..5 tiles, each 2..5 by 2..5')
    asymmetric = False
    for ra, rb in rs:
        for ca, cb in cs:
            tile = [list(row[ca:cb]) for row in grid[ra:rb]]
            if not any(v == fg for row in tile for v in row):
                errors.append('every tile must contain foreground marks')
            asymmetric |= any(row != row[::-1] for row in tile)
    if not asymmetric:
        errors.append('all tiles are LR-symmetric; mirror would be invisible')
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid) != 3 or len(grid[0]) != 11:
        return ['strict profile: one row of three 3x3 tiles']
    return []


def _partial_reflection(grid, *, only_color4=False, first_row=False,
                        first_three_columns=False, fixed_width3=False, outer_only=False, vertical=False):
    """Declared counterfactuals only; never used to supply generated labels."""
    rs, cs, fg = _layout(grid)
    out = [list(row) for row in grid]
    if only_color4 and fg != 4:
        return out
    for tr, (ra, rb) in enumerate(rs):
        for tc, (ca, cb) in enumerate(cs):
            if (first_row and tr > 0) or (first_three_columns and tc >= 3):
                continue
            if outer_only:
                for r in range(ra, rb):
                    out[r][ca], out[r][cb - 1] = grid[r][cb - 1], grid[r][ca]
                continue
            if fixed_width3:
                if cb - ca >= 3:
                    for r in range(ra, rb):
                        out[r][ca], out[r][ca + 2] = grid[r][ca + 2], grid[r][ca]
                continue
            for r in range(ra, rb):
                for c in range(ca, cb):
                    out[r][c] = grid[ra + rb - 1 - r][c] if vertical else grid[r][ca + cb - 1 - c]
    return out


def _color4_only(grid):
    return _partial_reflection(grid, only_color4=True)


def _first_row_only(grid):
    return _partial_reflection(grid, first_row=True)


def _first_three_columns(grid):
    return _partial_reflection(grid, first_three_columns=True)


def _fixed_width3(grid):
    return _partial_reflection(grid, fixed_width3=True)


def _outer_columns_only(grid):
    return _partial_reflection(grid, outer_only=True)


def _vertical_in_tiles(grid):
    return _partial_reflection(grid, vertical=True)


def _identity(grid):
    return [list(row) for row in grid]


def _global_lr(grid):
    return [list(row)[::-1] for row in grid]


def _edge_witness(grid, region):
    rs, cs, fg = _layout(grid)
    return any(grid[r][ca] != grid[r][cb - 1]
               for tr, (ra, rb) in enumerate(rs) for tc, (ca, cb) in enumerate(cs)
               if region(tr, tc, cb - ca, fg) for r in range(ra, rb))


def _width_witness(grid):
    return _edge_witness(grid, lambda tr, tc, width, fg: width != 3)


def _interior_witness(grid):
    rs, cs, fg = _layout(grid)
    return any(cb - ca >= 4 and grid[r][ca + 1] != grid[r][cb - 2]
               for ra, rb in rs for ca, cb in cs for r in range(ra, rb))


def _row_witness(grid):
    return _edge_witness(grid, lambda tr, tc, width, fg: tr > 0)


def _column_witness(grid):
    return _edge_witness(grid, lambda tr, tc, width, fg: tc >= 3)


def _color_witness(grid):
    return _edge_witness(grid, lambda tr, tc, width, fg: fg != 4)


CANONICAL_SHORTCUTS = {
    'swap_outer_columns_only': _outer_columns_only,
    'swap_first_third_columns_only': _fixed_width3,
    'first_tile_row_only': _first_row_only,
    'first_three_tile_columns_only': _first_three_columns,
    'color4_only': _color4_only,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES = {
    'reflect_interior_columns': _interior_witness,
    'variable_tile_width': _width_witness,
    'additional_tile_rows': _row_witness,
    'additional_tile_columns': _column_witness,
    'foreground_color_independence': _color_witness,
}
WITNESS_RIVALS = {
    'reflect_interior_columns': ['swap_outer_columns_only'],
    'variable_tile_width': ['swap_first_third_columns_only'],
    'additional_tile_rows': ['first_tile_row_only'],
    'additional_tile_columns': ['first_three_tile_columns_only'],
    'foreground_color_independence': ['color4_only'],
}
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS, identity=_identity,
                          whole_grid_lr=_global_lr, vertical_in_tiles=_vertical_in_tiles)


def lesson_identifiable(demos, query):
    """Finite declared-rival check, not a universal uniqueness certificate."""
    return [f'{name} fits demonstrations but changes the query'
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(p['input']) == p['output'] for p in demos)
            and rival(query['input']) != query['output']]


def _draw_from_degenerate(name, rng):
    """Diagnostic negative fixtures, deliberately outside the generate API."""
    if name == 'lr_symmetric_tiles':
        tile = [[4, 0, 4], [0, 4, 0], [4, 0, 4]]
        return assemble_tiles([[tile, tile, tile]])
    if name == 'empty_tiles':
        return assemble_tiles([[blank_tile() for _ in range(3)]])
    if name == 'no_tiles':
        return [[9] * 3 for _ in range(3)]
    raise ValueError(f'unknown diagnostic texture: {name}')
