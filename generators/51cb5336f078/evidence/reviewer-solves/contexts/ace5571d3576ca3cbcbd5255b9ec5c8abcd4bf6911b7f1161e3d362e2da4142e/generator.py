"""Input sampler for E152: REPLACE one object by its bounding-box frame.

The canonical Racket rule starts from an empty canvas: original interior cells
are erased, not preserved. This module emits inputs only. Rival functions below
are deliberately incorrect hypotheses for lesson checks, never label authority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = '51cb5336f078'
RULE_HASH = '2bb5c38e3f24'
VERSION = '3.0.0'
SUMMARY = (
    'One connected monochrome object on zero background; replace it with its '
    'tight bounding-box outline in the original color, erasing its interior. '
    'Vary canvas, color, occupancy, shape and position. Alternate bent-interior '
    'teaching witnesses with unconstrained nonidentity motifs.'
)
INVARIANTS = [
    'background is 0; exactly one 4-connected nonzero-color object',
    'canvas is 5..12 by 5..12; object has exactly 3..18 occupied cells',
    'the object is not already precisely its bounding-box frame',
    'default even-index draws contain an interior cell on neither a complete vertical nor horizontal stroke',
]
AXES = {
    'grid_h': {'type': 'int', 'default': '5..12; half draws favor canonical height 5', 'valid': '5..12'},
    'grid_w': {'type': 'int', 'default': '5..12; half draws favor canonical widths 5..7', 'valid': '5..12'},
    'motif_size': {'type': 'int', 'default': '3..18; teaching draws 5..18; canonical component favors 6..7', 'valid': '3..18'},
    'color': {'type': 'int', 'default': 'uniform 1..9', 'valid': '1..9'},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ('bent_interior', 'broad')


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 2]


def _bbox(cells):
    return min(r for r, c in cells), min(c for r, c in cells), max(r for r, c in cells), max(c for r, c in cells)


def _bbox_outline_cells(cells):
    top, left, bottom, right = _bbox(cells)
    return {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
            if r in (top, bottom) or c in (left, right)}


def _bbox_outline_missing(cells):
    return bool(_bbox_outline_cells(cells) - set(cells))


def _cells(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}


def _bent_interior(cells):
    edge = _bbox_outline_cells(cells)
    return any(not ({(r-1, c), (r+1, c)} <= cells)
               and not ({(r, c-1), (r, c+1)} <= cells) for r, c in cells - edge)


def _grow(rng, h, w, size, initial, blocked=()):
    """Bounded frontier growth: each iteration adds exactly one connected cell."""
    cells, blocked = set(initial), set(blocked)
    for _ in range(size - len(cells)):
        frontier = {(r+dr, c+dc) for r, c in cells
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= r+dr < h and 0 <= c+dc < w}
        candidates = sorted(frontier - cells - blocked)
        if not candidates:
            raise RuntimeError('connected-growth frontier unexpectedly exhausted')
        cells.add(rng.choice(candidates))
    return cells


def _draw_motif(rng, h, w, size, witness):
    for _ in range(128):
        cells = _grow(rng, h, w, size, [(rng.randrange(h), rng.randrange(w))])
        if cells != _bbox_outline_cells(cells) and (not witness or _bent_interior(cells)):
            return cells
    # A connected staircase has a genuine bent interior. Keep two neighboring
    # cells blank while growing, so its witness survives even at size 18 on 5x5.
    initial = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]
    if size < 5:
        return set(initial[:size])  # size 3 is L-shaped; size 4 has bbox 2x3.
    cells = _grow(rng, h, w, size, initial, blocked=[(1, 0), (2, 1)])
    # Mirrors preserve witness semantics and avoid a fixed fallback corner.
    if rng.randrange(2):
        cells = {(h-1-r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, w-1-c) for r, c in cells}
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f'unknown override axes: {sorted(unknown)}')
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f'{name} must be an integer, not {type(value).__name__}')
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = ctx.draw_choice('curriculum_component', ('canonical_scale', 'broad')) == 'canonical_scale'
    h = ctx.draw_choice('grid_h', list(range(5, 13)) + ([5] * 120 if core else []))
    w = ctx.draw_choice('grid_w', list(range(5, 13)) + ([5, 6, 7] * 40 if core else []))
    teaching = schedule_profile(seed, sample_index, difficulty) == 'bent_interior'
    # All exact values stay in the options in every band. A caller requesting
    # 3 or 4 cells explicitly opts out of the default interior-witness schedule.
    favored = list(range(5, 9)) if difficulty == 'easy' else (
        list(range(10, 19)) if difficulty == 'hard' else list(range(5, 15)))
    size_options = list(range(3, 19)) + ([6, 7] * 30 if core else favored * 3)
    if teaching and overrides.get('motif_size') is None:
        size_options = [value for value in size_options if value >= 5]
    size = ctx.draw_choice('motif_size', size_options)
    color = ctx.draw_int('color', 1, 9)
    cells = _draw_motif(ctx.draw_rng('layout'), h, w, size, teaching and size >= 5)
    grid = full_grid(h, w, 0)
    for r, c in cells:
        grid[r][c] = color
    return grid


def observe_overrides(grid):
    cells = _cells(grid)
    return {'grid_h': len(grid), 'grid_w': len(grid[0]), 'motif_size': len(cells),
            'color': grid[min(cells)[0]][min(cells)[1]]}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ['grid must be nonempty and rectangular']
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ['grid rows must have equal width']
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ['cells must be integer colors 0..9 (not booleans)']
    if not (5 <= len(grid) <= 12 and 5 <= len(grid[0]) <= 12):
        return ['canvas must be 5..12 by 5..12']
    colors = {v for row in grid for v in row if v}
    if len(colors) != 1:
        return ['expected exactly one nonzero color']
    cells = _cells(grid)
    if not 3 <= len(cells) <= 18:
        return [f'expected 3..18 motif cells, found {len(cells)}']
    reached = {min(cells)}
    frontier = list(reached)
    while frontier:
        r, c = frontier.pop()
        for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if point in cells and point not in reached:
                reached.add(point)
                frontier.append(point)
    if reached != cells:
        return ['expected exactly one 4-connected object']
    if cells == _bbox_outline_cells(cells):
        return ['object already equals its bounding-box frame; identity instance']
    return []


def strict_canonical_like(grid):
    """Task-domain check, not an exact-canvas check; broad variants stay lawful."""
    return self_check(grid)


def _rival_overlay(grid):
    out = [list(row) for row in grid]
    cells = _cells(grid)
    color = grid[min(cells)[0]][min(cells)[1]]
    for r, c in _bbox_outline_cells(cells):
        out[r][c] = color
    return out


def _rival_solid(grid):
    out = [list(row) for row in grid]
    cells = _cells(grid)
    top, left, bottom, right = _bbox(cells)
    color = grid[min(cells)[0]][min(cells)[1]]
    for r in range(top, bottom+1):
        for c in range(left, right+1):
            out[r][c] = color
    return out


def _rival_vertical_stroke(grid):
    """Canonical-fitting shortcut: erase only pixels within vertical strokes."""
    out = _rival_overlay(grid)
    cells = _cells(grid)
    for r, c in cells - _bbox_outline_cells(cells):
        if {(r-1, c), (r+1, c)} <= cells:
            out[r][c] = 0
    return out


def _rival_identity(grid):
    return [list(row) for row in grid]


def _has_interior(grid):
    cells = _cells(grid)
    return bool(cells - _bbox_outline_cells(cells))


def _has_bent_interior(grid):
    return _bent_interior(_cells(grid))


SEMANTIC_WITNESSES = {'erase_interior': _has_interior, 'bent_interior': _has_bent_interior}
SEMANTIC_RIVALS = {
    'overlay_frame': _rival_overlay, 'solid_bbox': _rival_solid,
    'erase_vertical_stroke_only': _rival_vertical_stroke, 'identity': _rival_identity,
}
WITNESS_RIVALS = {
    'erase_interior': ['overlay_frame', 'solid_bbox'],
    'bent_interior': ['erase_vertical_stroke_only'],
}
CANONICAL_SHORTCUTS = {'erase_vertical_stroke_only': _rival_vertical_stroke}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite rival check using supplied demonstration labels, not private labels."""
    return [f'{name} is not refuted by demonstrations'
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair['input']) == pair['output'] for pair in demos)]
