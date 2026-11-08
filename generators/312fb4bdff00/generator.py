"""H158: normalized dihedral matching, preserving the winning panel's placement.

The Racket rule compares translation-normalized supports, then returns the FIRST
matching candidate under the FIRST successful D4 transform, WITHOUT normalizing
its output location. Generate inputs only; Racket remains the label authority.

The three-phase default curriculum supplies multiple matches, guaranteed absence,
and translated single matches. Five consecutive examples cover every phase; a
six-pair lesson contains two of each, so rotating any pair into query retains a
precedence, translated-single, and no-match-sentinel witness. Explicit overrides
describe individual cases and are not promised to preserve this teaching schedule.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = '312fb4bdff00'
TASK_ID = GENERATOR_ID
VERSION = '3.1.0'
RULE_HASH = 'cc8c5c7301a4'
SUMMARY = (
    'Match translation-normalized panel supports under ordered D4 transforms; '
    'recolor the first matching transformed candidate, preserving its position. '
    'Teach same-count decoys, no match, translated matches and first-candidate precedence.'
)
INVARIANTS = [
    'one nonzero header target; 2..5 square body panels separated by full-height 8 columns',
    'panel side 3..6 and total width at most 30; every panel has 2..8 occupied cells',
    'matching uses normalized support, not color, count alone, or absolute position',
    'ordinary draws include zero, one and multiple matches; outputs remain Racket-derived',
]
AXES = {
    'panel_s': {'type':'int','default':'core 4; broad 3..6','valid':'3..6'},
    'n_cands': {'type':'int','default':'core 3; broad 1..4 subject to canvas','valid':'1..4'},
    'shape_k': {'type':'int','default':'2..8, with translation room in default draws','valid':'2..8'},
    'match_count': {'type':'int','default':'schedule: 2, 0, 1','valid':'0..4'},
    'target_color': {'type':'int','default':'uniform 1..9','valid':'1..9'},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {'panel_s':6,'n_cands':4}, {'panel_s':6,'match_count':4},
    {'n_cands':1,'match_count':[2,3,4]},
    {'n_cands':2,'match_count':[3,4]},
    {'n_cands':3,'match_count':4},
]
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ('multiple','absence','translated_single')
_CARD = ((-1,0),(1,0),(0,-1),(0,1))


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[(int(seed) + sample_index) % len(SCHEDULE_PROFILES)]


def _norm(cells):
    if not cells:
        return ()
    mr,mc = min(r for r,c in cells),min(c for r,c in cells)
    return tuple(sorted((r-mr,c-mc) for r,c in cells))


def _xform(cells, name, s):
    """Same ordered D4 names as the authority; coordinates retain the full box."""
    if name == 0: return tuple(sorted(cells))
    if name == 1: return tuple(sorted((c,s-1-r) for r,c in cells))
    if name == 2: return tuple(sorted((s-1-r,s-1-c) for r,c in cells))
    if name == 3: return tuple(sorted((s-1-c,r) for r,c in cells))
    if name == 4: return tuple(sorted((r,s-1-c) for r,c in cells))
    if name == 5: return tuple(sorted((s-1-r,c) for r,c in cells))
    if name == 6: return tuple(sorted((c,r) for r,c in cells))
    return tuple(sorted((s-1-c,s-1-r) for r,c in cells))


def _shift(cells, r0, c0):
    return tuple(sorted((r+r0,c+c0) for r,c in cells))


def _placements(cells, s):
    shape = _norm(cells)
    h,w = max(r for r,c in shape)+1,max(c for r,c in shape)+1
    return tuple(_shift(shape,r,c) for r in range(s-h+1) for c in range(s-w+1))


@lru_cache(maxsize=2048)
def _matching_options(shape, s):
    """Immutable legal supports plus FIRST-transform outputs, independent of seed."""
    options = {}
    for orientation in range(8):
        oriented = _norm(_xform(shape,orientation,s))
        transform = next(t for t in range(8) if _norm(_xform(oriented,t,s)) == shape)
        for placed in _placements(oriented,s):
            options[placed] = (placed,_xform(placed,transform,s))
    return tuple(options[key] for key in sorted(options))


def _build_shape(rng, s, k):
    # Favor a movable bounding box. Dense explicit overrides may necessarily
    # fill its height/width; their geometry is preserved, never clipped.
    side = s-1 if k <= (s-1)*(s-1) else s
    if rng.randrange(4):
        cells = {(rng.randrange(side),rng.randrange(side))}
        while len(cells) < k:
            frontier = sorted({(r+dr,c+dc) for r,c in cells for dr,dc in _CARD
                               if 0 <= r+dr < side and 0 <= c+dc < side} - cells)
            cells.add(rng.choice(frontier))
    else:
        cells = set(rng.sample([(r,c) for r in range(side) for c in range(side)],k))
    return _norm(cells)


def _decoy(rng, shape, s, k):
    forbidden = {_norm(_xform(shape,t,s)) for t in range(8)}
    points = [(r,c) for r in range(s) for c in range(s)]
    for _ in range(64):
        cells = tuple(sorted(rng.sample(points,k)))
        if _norm(cells) not in forbidden:
            return cells
    # Exact, bounded fallback. There are at most 8*s*s congruent supports,
    # so inspecting that many + 1 distinct k-subsets must find a nonmatch
    # whenever another congruence class exists (all advertised (s,k) have one).
    for index,cells in enumerate(combinations(points,k)):
        if _norm(cells) not in forbidden:
            return cells
        if index >= 8*s*s:
            break
    raise RuntimeError('No equal-count decoy found in the declared finite domain')


def _validate_overrides(overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f'unknown override axes: {sorted(unknown)}; see AXES for v3 exact controls')
    clean = {name:value for name,value in overrides.items() if value is not None}
    for name,value in clean.items():
        lo,hi = map(int,AXES[name]['valid'].split('..'))
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f'{name} must be an integer in [{lo}, {hi}]')
    for combination in INCOMPATIBLE_OVERRIDE_COMBINATIONS:
        if all(key in clean and clean[key] in (value if isinstance(value,list) else [value])
               for key,value in combination.items()):
            raise ValueError(f'incompatible overrides: {combination}')
    return clean


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,
                  difficulty=difficulty,overrides=overrides)
    mode = schedule_profile(seed,sample_index,difficulty)
    core = ctx.draw_choice('curriculum_scale',('core','core','core','broad')) == 'core'
    required = max(overrides.get('n_cands',1),overrides.get('match_count',0))
    sides = [s for s in range(3,7) if (required+1)*(s+1)-1 <= 30]
    favorites = [4]*20 if core else ([3,4] if difficulty == 'easy' else [5,6])
    s = ctx.draw_choice('panel_s',sides+[v for v in favorites if v in sides])
    minimum = max(1,overrides.get('match_count',0))
    if mode == 'multiple' and 'n_cands' not in overrides:
        minimum = max(2,minimum)
    counts = [n for n in range(minimum,5) if (n+1)*(s+1)-1 <= 30]
    n = ctx.draw_choice('n_cands',counts+([3]*20 if core and 3 in counts else []))
    k_options = list(range(2,min(8,(s-1)*(s-1))+1))
    # Explicit dense cases remain valid even though default teaching draws
    # deliberately reserve translation room.
    if 'shape_k' in overrides and overrides['shape_k'] not in k_options:
        k_options.append(overrides['shape_k'])
    if core: k_options += [min(4,max(k_options))]*4
    k = ctx.draw_choice('shape_k',k_options)
    desired = {'multiple':2,'absence':0,'translated_single':1}[mode]
    count = ctx.draw_choice('match_count',
                            [overrides['match_count']] if 'match_count' in overrides else [min(n,desired)])
    target = ctx.draw_int('target_color',1,9)
    rng = ctx.draw_rng('layout')
    shape = _build_shape(rng,s,k)
    query = rng.choice(_placements(shape,s))
    options = _matching_options(shape,s)
    shifted = [pair for pair in options if pair[1] != query and pair[1] != shape]
    align = mode == 'absence' or (mode == 'multiple' and rng.randrange(4) == 0)
    first_pool = ([pair for pair in options if pair[1] == query] if align else shifted)
    first = rng.choice(first_pool or options)
    selected = [first] if count else []
    for index in range(1,count):
        distinct = [pair for pair in options if pair[1] != first[1]]
        selected.append(rng.choice(distinct or options))
    slots = sorted(rng.sample(range(n),count))
    answer_by_slot = {slot:selected[i][0] for i,slot in enumerate(slots)}
    candidates = []
    for i in range(n):
        if i in answer_by_slot:
            candidates.append(answer_by_slot[i])
        else:
            # The absence phase is always equal-count, so counting is no test
            # for existence. Other phases also retain different-count distractors.
            dk = k if count == 0 or rng.randrange(4) else rng.randint(2,8)
            candidates.append(_decoy(rng,shape,s,dk))
    all_panels = [query]+candidates
    width = (n+1)*(s+1)-1
    grid = full_grid(s+1,width,0)
    grid[0][rng.randrange(width)] = target
    colors = [c for c in range(1,10) if c not in (8,target)]
    rng.shuffle(colors)
    for index,cells in enumerate(all_panels):
        color = colors[index]
        # Color 8 may be an object color, as in the canonical query. Never
        # introduce an accidental full separator inside a panel.
        if rng.randrange(6) == 0 and not any(all((r,c) in cells for r in range(s)) for c in range(s)):
            color = 8
        offset = index*(s+1)
        for r,c in cells:
            grid[r+1][offset+c] = color
        if index < n:
            for r in range(1,s+1): grid[r][offset+s] = 8
    return grid


def _parts(grid):
    if not isinstance(grid,(list,tuple)) or not grid or not grid[0]:
        raise ValueError('empty grid')
    if any(not isinstance(row,(list,tuple)) or len(row) != len(grid[0]) for row in grid):
        raise ValueError('ragged grid')
    if any(type(x) is not int or not 0 <= x <= 9 for row in grid for x in row):
        raise ValueError('grid colors must be integers in 0..9')
    s,w = len(grid)-1,len(grid[0])
    if not 3 <= s <= 6 or w > 30:
        raise ValueError('expected panel side 3..6 and ARC width at most 30')
    header = [x for x in grid[0] if x]
    if len(header) != 1:
        raise ValueError('expected exactly one nonzero header target')
    cuts = [c for c in range(w) if all(grid[r][c] == 8 for r in range(1,s+1))]
    boundaries = [-1]+cuts+[w]
    if not 1 <= len(cuts) <= 4 or any(b-a-1 != s for a,b in zip(boundaries,boundaries[1:])):
        raise ValueError('expected 2..5 equal square panels and single separator columns')
    panels = [tuple((r,c-a-1) for r in range(s) for c in range(a+1,b) if grid[r+1][c])
              for a,b in zip(boundaries,boundaries[1:])]
    if any(not 2 <= len(panel) <= 8 for panel in panels):
        raise ValueError('each panel must contain 2..8 cells')
    return s,header[0],panels


def _hits(s, panels):
    q = _norm(panels[0])
    hits = []
    for i,candidate in enumerate(panels[1:]):
        for t in range(8):
            transformed = _xform(candidate,t,s)
            if _norm(transformed) == q:
                hits.append((i,t,transformed));break
    return hits


def self_check(grid, *, difficulty=None, meta=None):
    try: _parts(grid)
    except (ValueError,TypeError,IndexError) as exc: return [str(exc)]
    return []


def strict_canonical_like(grid):
    """Lawful square-panel task instances, including the authority's no-match case."""
    return self_check(grid)


def observe_overrides(grid):
    s,target,panels = _parts(grid)
    return {'panel_s':s,'n_cands':len(panels)-1,'shape_k':len(panels[0]),
            'match_count':len(_hits(s,panels)),'target_color':target}


def _paint_support(cells, s, target):
    occupied = set(cells)
    return [[target if (r,c) in occupied else 0 for c in range(s)] for r in range(s)]


def _query_copy(grid):
    s,target,panels = _parts(grid)
    return _paint_support(panels[0],s,target)


def _existence_gated_copy(grid):
    s,target,panels = _parts(grid)
    return _query_copy(grid) if _hits(s,panels) else [[0]]


def _last_match(grid):
    s,target,panels = _parts(grid);hits = _hits(s,panels)
    return _paint_support(hits[-1][2],s,target) if hits else [[0]]


def _single_match_copy(grid):
    """Rival: handles precedence correctly but wrongly copies unique matches."""
    s,target,panels = _parts(grid);hits = _hits(s,panels)
    if not hits: return [[0]]
    return _query_copy(grid) if len(hits) == 1 else _paint_support(hits[0][2],s,target)


def _copy_query_on_absence(grid):
    """Rival: matches correctly, but replaces the no-match sentinel with the query."""
    s,target,panels = _parts(grid);hits = _hits(s,panels)
    return _paint_support(hits[0][2],s,target) if hits else _query_copy(grid)


def _normalized_first(grid):
    s,target,panels = _parts(grid);hits = _hits(s,panels)
    return _paint_support(_norm(hits[0][2]),s,target) if hits else [[0]]


def _count_only_copy(grid):
    s,target,panels = _parts(grid)
    return _query_copy(grid) if any(len(p) == len(panels[0]) for p in panels[1:]) else [[0]]


def _translated(grid):
    s,target,panels = _parts(grid);hits = _hits(s,panels)
    return bool(hits and hits[0][2] != tuple(sorted(panels[0])))


def _nonzero_offset(grid):
    s,target,panels = _parts(grid);hits = _hits(s,panels)
    return bool(hits and hits[0][2] != _norm(hits[0][2]))


def _precedence(grid):
    s,target,panels = _parts(grid);hits = _hits(s,panels)
    return bool(len(hits)>1 and hits[0][2] != hits[-1][2])


def _unique_translated(grid):
    s,target,panels = _parts(grid);hits = _hits(s,panels)
    return len(hits) == 1 and hits[0][2] != tuple(sorted(panels[0]))


def _absent_same_count(grid):
    s,target,panels = _parts(grid)
    return not _hits(s,panels) and any(len(p) == len(panels[0]) for p in panels[1:])


CANONICAL_SHORTCUTS = {
    'copy_query':_query_copy,
    'existence_gated_copy':_existence_gated_copy,
    'last_matching_candidate':_last_match,
    'normalize_output_position':_normalized_first,
    'count_only_copy':_count_only_copy,
    'copy_unique_match_only':_single_match_copy,
    'copy_query_on_absence':_copy_query_on_absence,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES = {
    'translated_match':_translated,
    'translated_unique_match':_unique_translated,
    'preserve_output_offset':_nonzero_offset,
    'first_candidate_precedence':_precedence,
    'absent_equal_count_match':_absent_same_count,
}
WITNESS_RIVALS = {
    'translated_match':['copy_query','existence_gated_copy'],
    'translated_unique_match':['copy_unique_match_only'],
    'preserve_output_offset':['normalize_output_position'],
    'first_candidate_precedence':['last_matching_candidate'],
    'absent_equal_count_match':['count_only_copy','copy_query_on_absence'],
}
