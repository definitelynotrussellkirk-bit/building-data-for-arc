"""Fill hollow cardinal crosses, with exact knobs and contrastive distractors.

4.0 removes five advertised-but-inert axes (palette_kind, palette_size,
position_bias, n_distinct_colors, density) rather than pretending they work.
All accepted numeric overrides are exact; incompatible packing raises ValueError.
Racket remains the label authority. Python predicates only validate input
structure or deliberately implement rival hypotheses for semantic checks.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = 'f9dd4cf0f344'
TASK_ID = 'f9dd4cf0f344'
VERSION = '4.0.0'
RULE_HASH = '2dc205754ece'
SUMMARY = (
    'Fill an interior zero cell exactly when its four cardinal neighbors have '
    'one common nonzero color. Canonical-style sparse crosses are mixed with '
    'three-plus-one color near misses, occupied centers, partial arms, and '
    'diagonal-only decoys. Counts and dimensions are exact; zero stays background.'
)
INVARIANTS = [
    'rectangular integer grid with values in 0..9 and background 0',
    'default draws contain at least one fillable cardinal-cross center',
    'only intended hollow cardinal crosses fire; decoy centers never fire',
    'accepted dimension and motif-count overrides equal their realized values',
]
HELPFUL_TEXTURES = ('plain', 'mixed', 'near_miss', 'occupied', 'diagonal')
DEGENERATE_TEXTURES = ('no_pluses', 'partial_arms', 'mismatched_arms')
# These are explicit identity controls, never selected for default training.
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
AXES = {
    'grid_h': {'type':'int', 'default':'7..8 anchor; 7..10 easy; 10..14 medium; 13..22 hard', 'valid':'5..22'},
    'grid_w': {'type':'int', 'default':'7..9 anchor; 7..10 easy; 10..14 medium; 13..22 hard', 'valid':'5..22'},
    'pluses': {'type':'int', 'default':'2 anchor; 1..3 easy; 2..4 medium; 3..6 hard; explicit negative controls 0', 'valid':'0..8'},
    'n_decoys': {'type':'int', 'default':'0 anchor; 1..2 easy/medium; 2..3 hard, bounded by available slots', 'valid':'0..8'},
    'texture': {'type':'str', 'default':'keyed mix, one-third plain anchors',
                'valid':'|'.join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []  # exceptions identify actual conflicting axes
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_COLORS = tuple(range(1, 10))


def _incompatible(message, *axes):
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    raise exc


def _integer(ctx, name, lo, hi, defaults):
    # GenCtx casts int overrides; reject booleans/floats/strings BEFORE that cast.
    if name in ctx.overrides:
        value = ctx.overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            _incompatible(f'{name} must be an integer in {lo}..{hi}', name)
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, *defaults)


def _arms(grid, r, c, offsets=_CARD):
    return [grid[r+dr][c+dc] for dr, dc in offsets]


def _fires(grid):
    """Input-side placement postcondition, not a training-label producer."""
    return {(r,c) for r in range(1,len(grid)-1) for c in range(1,len(grid[0])-1)
            if grid[r][c] == 0 and len(set(_arms(grid,r,c))) == 1
            and grid[r-1][c] != 0}


def _decoy_kind(grid, r, c):
    vals = _arms(grid,r,c)
    nonzero = [v for v in vals if v != 0]
    if len(nonzero) == 4:
        if len(set(vals)) == 1 and grid[r][c] not in (0, vals[0]):
            return 'occupied'
        if grid[r][c] == 0 and len(set(vals)) > 1:
            return 'near_miss' if max(vals.count(k) for k in vals) == 3 else 'mismatched_arms'
    if grid[r][c] == 0 and len(nonzero) == 3 and len(set(nonzero)) == 1:
        return 'partial_arms'
    diagonal = _arms(grid,r,c,_DIAG)
    if (grid[r][c] == 0 and not nonzero and diagonal[0] != 0
            and len(set(diagonal)) == 1):
        return 'diagonal'
    return None


def observe_overrides(grid):
    """Recover exact numeric axes from pixels, not draw provenance."""
    return {'grid_h':len(grid), 'grid_w':len(grid[0]), 'pluses':len(_fires(grid)),
            'n_decoys':sum(_decoy_kind(grid,r,c) is not None
                           for r in range(1,len(grid)-1) for c in range(1,len(grid[0])-1))}


def _slots(h, w, rng):
    # Disjoint 3x3 motif boxes separated by a blank row/column. Random phase
    # exposes every edge while a constructive capacity bound avoids rejection.
    nr, nc = (h+1)//4, (w+1)//4
    r0 = rng.randint(1, h-2-4*(nr-1))
    c0 = rng.randint(1, w-2-4*(nc-1))
    slots = [(r0+4*r,c0+4*c) for r in range(nr) for c in range(nc)]
    rng.shuffle(slots)
    return slots


def _paint_decoy(grid, r, c, kind, color, rng):
    other = rng.choice([v for v in _COLORS if v != color])
    if kind == 'diagonal':
        for dr,dc in _DIAG:
            grid[r+dr][c+dc] = color
        return
    vals = [color]*4
    j = rng.randrange(4)
    if kind == 'partial_arms':
        vals[j] = 0
    elif kind == 'near_miss':
        vals[j] = other
    elif kind == 'mismatched_arms':
        vals = [color,color,other,other]
        rng.shuffle(vals)
    elif kind == 'occupied':
        grid[r][c] = other
    else:
        raise ValueError(f'unknown decoy kind: {kind}')
    for (dr,dc), value in zip(_CARD,vals):
        grid[r+dr][c+dc] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f'unknown or removed override axes: {sorted(unknown)}; supported: {sorted(AXES)}')
    if difficulty not in (None,'easy','medium','hard'):
        raise ValueError('difficulty must be None, easy, medium, or hard')
    for name in ('grid_h','grid_w','pluses','n_decoys'):
        if name in overrides:
            lo,hi = (5,22) if name.startswith('grid_') else (0,8)
            if type(overrides[name]) is not int or not lo <= overrides[name] <= hi:
                _incompatible(f'{name} must be an integer in {lo}..{hi}',name)
    if 'texture' in overrides and overrides['texture'] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError(f'unknown texture {overrides["texture"]!r}')
    ctx = gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,
                  task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    # Three of nine equal draw entries preserve anchors in EVERY difficulty.
    textures = ('plain','plain','plain','mixed','mixed','mixed','near_miss','occupied','diagonal')
    if 'texture' in overrides:
        textures = HELPFUL_TEXTURES + DEGENERATE_TEXTURES
    elif overrides.get('n_decoys',0) > 0:
        textures = tuple(t for t in textures if t != 'plain')
    texture = ctx.draw_choice('texture',textures)
    negative = texture in DEGENERATE_TEXTURES
    if negative and overrides.get('pluses',0) > 0:
        _incompatible('texture is an identity control and requires pluses=0','texture','pluses')
    if texture in ('plain','no_pluses') and overrides.get('n_decoys',0) > 0:
        _incompatible('plain/no_pluses texture requires n_decoys=0','texture','n_decoys')
    if texture == 'plain':
        hr,wr,pr,drange = (7,8),(7,9),(2,2),(0,0)
    elif difficulty == 'easy':
        hr,wr,pr,drange = (7,10),(7,10),(1,3),(1,2)
    elif difficulty == 'hard':
        hr,wr,pr,drange = (13,22),(13,22),(3,6),(2,3)
    else:
        hr,wr,pr,drange = (10,14),(10,14),(2,4),(1,2)
    # Satisfy requested counts by drawing feasible UNPINNED dimensions. A lone
    # pluses=8 is not an incompatibility: the caller left room to enlarge the
    # canvas. Conversely a pinned 5x5 never silently turns into a larger grid.
    reserve = overrides.get('n_decoys',0)
    required = overrides.get('pluses',0 if negative else 1) + reserve
    if 'grid_h' in overrides:
        hr = (overrides['grid_h'],)*2
    if 'grid_w' in overrides:
        wr = (overrides['grid_w'],)*2
    def fits(h,w):
        return ((h+1)//4)*((w+1)//4) >= required
    if not fits(hr[1],wr[1]):
        if 'grid_h' not in overrides:
            hr = (hr[0],22)
        if 'grid_w' not in overrides:
            wr = (wr[0],22)
    if not fits(hr[1],wr[1]):
        involved = tuple(k for k in overrides if k in ('grid_h','grid_w','pluses','n_decoys'))
        _incompatible('requested counts do not fit pinned grid dimensions within 5..22',*involved)
    hmin = next(h for h in range(hr[0],hr[1]+1) if fits(h,wr[1]))
    h = _integer(ctx,'grid_h',5,22,(hmin,hr[1]))
    wmin = next(w for w in range(wr[0],wr[1]+1) if fits(h,w))
    w = _integer(ctx,'grid_w',5,22,(wmin,wr[1]))
    rng = ctx.draw_rng('layout')
    slots = _slots(h,w,rng)
    capacity = len(slots)
    pmax = min(pr[1],capacity-reserve)
    pdefaults = (0,0) if negative else (min(pr[0],pmax),pmax)
    pluses = _integer(ctx,'pluses',0,8,pdefaults)
    if negative and pluses:
        _incompatible('texture is an identity control and requires pluses=0','texture','pluses')
    if pluses + reserve > capacity:
        _incompatible('pluses+n_decoys exceed separated-slot capacity for grid_h/grid_w',
                      'pluses','n_decoys','grid_h','grid_w')
    dmax = min(drange[1],capacity-pluses)
    if texture == 'no_pluses':
        ddef = (0,0)
    elif negative:
        ddef = (min(2,capacity),min(2,capacity))
    else:
        ddef = (min(drange[0],dmax),dmax)
    n_decoys = _integer(ctx,'n_decoys',0,8,ddef)
    if texture in ('plain','no_pluses') and n_decoys:
        _incompatible('plain/no_pluses texture requires n_decoys=0','texture','n_decoys')
    if pluses+n_decoys > capacity:
        _incompatible('pluses+n_decoys exceed separated-slot capacity for grid_h/grid_w',
                      'pluses','n_decoys','grid_h','grid_w')
    grid = full_grid(h,w,0)
    colors = (rng.sample(_COLORS,pluses) if texture == 'plain'
              else [rng.choice(_COLORS) for _ in range(pluses)])
    intended = set(slots[:pluses])
    for (r,c),color in zip(slots,colors):
        for dr,dc in _CARD:
            grid[r+dr][c+dc] = color
    kinds = ['near_miss','occupied','partial_arms','diagonal','mismatched_arms']
    rng.shuffle(kinds)
    diagonal_colors = {}
    for i,(r,c) in enumerate(slots[pluses:pluses+n_decoys]):
        kind = kinds[i % len(kinds)] if texture == 'mixed' else texture
        # Two same-colored diagonal motifs four cells apart would create a
        # third diagonal-only center between them. Avoid precisely that local
        # coincidence rather than hiding it in the observer or resampling grids.
        forbidden = {color for (rr,cc),color in diagonal_colors.items()
                     if abs(r-rr)+abs(c-cc) == 4} if kind == 'diagonal' else set()
        color = rng.choice([k for k in _COLORS if k not in forbidden])
        _paint_decoy(grid,r,c,kind,color,rng)
        if kind == 'diagonal':
            diagonal_colors[(r,c)] = color
    actual = observe_overrides(grid)
    if _fires(grid) != intended or actual['n_decoys'] != n_decoys:
        raise RuntimeError('constructed motifs violate exact placement postcondition')
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid,(list,tuple)) or not grid:
        return ['grid must have rows']
    if not all(isinstance(row,(list,tuple)) and row for row in grid):
        return ['grid must have nonempty rows']
    if len({len(row) for row in grid}) != 1:
        return ['grid must be rectangular']
    if not (3 <= len(grid) <= 30 and 3 <= len(grid[0]) <= 30):
        return ['grid dimensions must be in 3..30 for this motif domain']
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ['grid values must be integers in 0..9 (not booleans)']
    meta = meta or {}
    explicit_identity = meta.get('texture') in DEGENERATE_TEXTURES or meta.get('pluses') == 0
    if not explicit_identity and not _fires(grid):
        return ['default teaching draw needs at least one fillable cardinal center']
    return []


def _draw_from_degenerate(name, rng=None):
    """Compatibility hook for negative-fixture tooling; fixed, lawful controls."""
    if name not in DEGENERATE_TEXTURES:
        raise ValueError(f'unknown negative fixture {name!r}')
    return generate(0,0,texture=name)


def _rival(grid, mode):
    """Deliberately wrong candidate rules, used ONLY for semantic diagnostics."""
    out = [row[:] for row in grid]
    for r in range(1,len(grid)-1):
        for c in range(1,len(grid[0])-1):
            vals = _arms(grid,r,c)
            same = vals[0] != 0 and len(set(vals)) == 1
            if same and (grid[r][c] == 0 or mode == 'overwrite'):
                out[r][c] = vals[0]
            if grid[r][c] != 0:
                continue
            if mode in ('majority','partial'):
                for k in _COLORS:
                    if vals.count(k) >= 3 and (mode == 'partial' or 0 not in vals):
                        out[r][c] = k
            if mode == 'diagonal':
                ds = _arms(grid,r,c,_DIAG)
                if ds[0] != 0 and len(set(ds)) == 1:
                    out[r][c] = ds[0]
    return out


def _majority_rival(grid):
    return _rival(grid,'majority')


def _overwrite_rival(grid):
    return _rival(grid,'overwrite')


def _partial_rival(grid):
    return _rival(grid,'partial')


def _diagonal_rival(grid):
    return _rival(grid,'diagonal')


def _has_kind(grid, kind):
    return any(_decoy_kind(grid,r,c) == kind
               for r in range(1,len(grid)-1) for c in range(1,len(grid[0])-1))


def _near_miss_witness(grid):
    return _has_kind(grid,'near_miss')


def _occupied_witness(grid):
    return _has_kind(grid,'occupied')


def _partial_witness(grid):
    return _has_kind(grid,'partial_arms')


def _diagonal_witness(grid):
    return _has_kind(grid,'diagonal')


SEMANTIC_RIVALS = {'enclosed_majority':_majority_rival, 'overwrite_occupied':_overwrite_rival,
                   'three_arms':_partial_rival, 'diagonals_also':_diagonal_rival}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {'near_miss':_near_miss_witness, 'occupied':_occupied_witness,
                      'partial':_partial_witness, 'diagonal':_diagonal_witness}
WITNESS_RIVALS = {'near_miss':['enclosed_majority'], 'occupied':['overwrite_occupied'],
                  'partial':['three_arms'], 'diagonal':['diagonals_also']}
