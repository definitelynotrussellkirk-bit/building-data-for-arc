"""Control-selected recoloring on separate rectangular frames and filled rectangles.

Only inputs are generated. Labels remain with canonical Racket rule 4441279127ff.
Every five-pair window has two contrasts per control and one broad layout;
see workspace/probe_distribution.py for finite rival and cyclic-window diagnostics.
"""
from __future__ import annotations

import hashlib
import itertools
import math
from functools import lru_cache, partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c7f337af82e5"
TASK_ID = GENERATOR_ID
RULE_HASH = "4441279127ff"
VERSION = "3.0.0"
SUMMARY = (
    "Read and clear the top-left control: 1 recolors hollow rectangular 7-frames "
    "to 8, while 2 recolors filled 7-rectangles. Generate 2..4 separate objects "
    "with both kinds, varied sizes and positions, and larger-solid counterexamples."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "8..16 rows and 9..18 columns; only background 0, control 1 or 2, and objects 7",
    "exactly one control at (0,0); 2..4 separate objects with at least one of each kind",
    "each object is an exact hollow rectangular frame or a filled rectangle",
    "all advertised dimensions, controls and object counts are jointly constructive",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical anchors plus band-weighted 8..16", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "canonical anchors plus band-weighted 9..18", "valid": "9..18"},
    "control": {"type": "int", "default": "balanced five-pair lesson coverage", "valid": "1..2"},
    "n_objects": {"type": "int", "default": "band-weighted 2..4", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("contrast_1", "contrast_2", "broad_1", "broad_2")
_PATTERN = ("contrast_1", "contrast_2", "contrast_1", "contrast_2", "broad_1",
            "contrast_1", "contrast_2", "contrast_1", "contrast_2", "broad_2")


def _phase(seed, sample_index):
    offset = int.from_bytes(hashlib.sha256(f"{TASK_ID}|{VERSION}|{seed}".encode()).digest()[:4], "big")
    return (offset + sample_index) % len(_PATTERN)


def schedule_profile(seed, sample_index, difficulty=None):
    """The default curriculum phase; explicit control overrides replace its selector."""
    return _PATTERN[_phase(seed, sample_index)]


def _axis(ctx, name, lo, hi, default):
    # Record the actual scheduled choice. Explicit values use the full legal range
    # in EVERY band; None retains GenCtx's documented no-override convention.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (default,))


@lru_cache(maxsize=4096)
def _placements(box, role):
    """Immutable feasible rectangles in a slot, excluding the control pixel."""
    r0, c0, r1, c1 = box
    hh, ww = r1 - r0, c1 - c0
    if role == "frame3":
        sizes = [(3, 3)]
    elif role == "rectangle":
        # 15-pixel nonsquare solids also match the 3x3 frame's perimeter 16.
        # A 3x4 solid is larger in area but would preserve the perimeter shortcut.
        sizes = [(3, 5), (5, 3)]
    elif role == "small":
        sizes = [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2)]
    else:
        sizes = [(h, w) for h in range(3, min(hh, 6) + 1)
                 for w in range(3, min(ww, 6) + 1)
                 if role != "solid" or h * w != 15]
    return tuple((r, c, h, w) for h, w in sizes if h <= hh and w <= ww
                 for r in range(r0, r1 - h + 1) for c in range(c0, c1 - w + 1)
                 if (r, c) != (0, 0))


def _shape_cells(r0, c0, hh, ww, *, kind):
    return {(r, c) for r in range(r0, r0 + hh) for c in range(c0, c0 + ww)
            if kind == "solid" or r in (r0, r0 + hh - 1) or c in (c0, c0 + ww - 1)}


def _layout(ctx, height, width, count, contrast):
    rng = ctx.draw_rng("layout")
    # Contrast slots guarantee a 3x5 solid clear of (0,0), even at 8x9.
    # The other three slots are at least 3x3, so all object counts remain feasible.
    row_cut = rng.randrange(4 if contrast else 3, height - 3)
    col_cut = rng.randrange(5 if contrast else 3, width - 3)
    boxes = [(r0, c0, r1, c1)
             for r0, r1 in ((0, row_cut), (row_cut + 1, height))
             for c0, c1 in ((0, col_cut), (col_cut + 1, width))]
    roles = ["frame3" if contrast else "frame",
             "rectangle" if contrast else rng.choice(("small", "solid"))]
    if count >= 3:
        roles.append("small" if contrast or count == 4 else rng.choice(("small", "frame")))
    if count == 4:
        roles.append("frame")
    possible = []
    for slots in itertools.permutations(range(4), count):
        pools = [_placements(boxes[slot], role) for slot, role in zip(slots, roles)]
        if not all(pools):
            continue
        if contrast:
            # Reverse BOTH canonical position ranks: the hollow object is right
            # of, and not above, the larger solid. Enforce this for all counts:
            # tied bottommost solids can otherwise keep a position rival alive.
            if slots[0] % 2 != 1 or slots[1] % 2 != 0:
                continue
            solids = tuple(p for p in pools[1] if p[0] <= max(f[0] for f in pools[0]))
            if not solids:
                continue
            pools[1] = solids
        possible.append(pools)
    if not possible:
        raise RuntimeError("constructive slot assignment failed for an advertised combination")
    pools = rng.choice(possible)
    chosen = [rng.choice(pool) for pool in pools]
    if contrast:
        chosen[0] = rng.choice([p for p in pools[0] if p[0] >= chosen[1][0]])
    grid = full_grid(height, width, 0)
    for role, (r, c, h, w) in zip(roles, chosen):
        kind = "hollow" if role.startswith("frame") else "solid"
        for rr, cc in _shape_cells(r, c, h, w, kind=kind):
            grid[rr][cc] = 7
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    phase = _phase(seed, sample_index)
    size_rng = ctx.draw_rng("canvas_size")
    anchors = ((8, 9), (11, 10))
    contrast = _PATTERN[phase].startswith("contrast")
    if phase % 5 in (0, 1):
        # Both controls see both canonical profiles across the ten-phase cycle.
        default_h, default_w = anchors[(phase % 5 + phase // 5) % 2]
    else:
        heights, widths = ((range(8, 12), range(9, 13)) if difficulty == "easy" else
                           ((range(11, 17), range(12, 19)) if difficulty == "hard" else
                            (range(8, 17), range(9, 19))))
        # Nearby contrasts for the same control alternate core/noncore sizes.
        # Broad scenes never contain a 15-pixel solid (_placements), so all
        # five default consecutive inputs are distinct before production dedup.
        choices = [(h, w) for h in heights for w in widths
                   if not contrast or (h, w) not in anchors]
        default_h, default_w = size_rng.choice(choices)
    height = _axis(ctx, "grid_h", 8, 16, default_h)
    width = _axis(ctx, "grid_w", 9, 18, default_w)
    control = _axis(ctx, "control", 1, 2, int(_PATTERN[phase][-1]))
    weights = (2, 2, 3, 4) if difficulty == "easy" else ((2, 3, 4, 4) if difficulty == "hard" else (2, 3, 4))
    count = _axis(ctx, "n_objects", 2, 4, ctx.draw_rng("object_count").choice(weights))
    grid = _layout(ctx, height, width, count, contrast)
    grid[0][0] = control
    return grid


def _components7(grid):
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7}
    result = []
    while pending:
        first = min(pending)
        pending.remove(first)
        stack, cells = [first], []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in pending:
                    pending.remove(p)
                    stack.append(p)
        result.append(cells)
    return result


def _bbox(cells):
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(cells):
    r0, c0, r1, c1 = _bbox(cells)
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _is_solid7(cells):
    return len(cells) == _bbox_area(cells)


def _is_hollow7(cells):
    r0, c0, r1, c1 = _bbox(cells)
    return r1 - r0 >= 2 and c1 - c0 >= 2 and set(cells) == _shape_cells(
        r0, c0, r1 - r0 + 1, c1 - c0 + 1, kind="hollow")


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "control": grid[0][0], "n_objects": len(_components7(grid))}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or value not in (0, 1, 2, 7) for row in grid for value in row):
        return ["cells must be integer colors 0, 1, 2, or 7"]
    errors = []
    if not 8 <= len(grid) <= 16 or not 9 <= len(grid[0]) <= 18:
        errors.append("grid is outside the declared 8..16 by 9..18 domain")
    if grid[0][0] not in (1, 2):
        errors.append("control cell (0,0) must be 1 or 2")
    if any(value in (1, 2) and (r, c) != (0, 0)
           for r, row in enumerate(grid) for c, value in enumerate(row)):
        errors.append("control colors may occur only at (0,0)")
    components = _components7(grid)
    if not 2 <= len(components) <= 4:
        errors.append("expected 2..4 separate 7-objects")
    if not any(_is_hollow7(cells) for cells in components):
        errors.append("missing hollow rectangular frame")
    if not any(_is_solid7(cells) for cells in components):
        errors.append("missing solid rectangle")
    if any(not (_is_hollow7(cells) or _is_solid7(cells)) for cells in components):
        errors.append("objects must be exact hollow frames or filled rectangles")
    return errors


def strict_canonical_like(grid):
    """Canonical-supported rectangular-object manifold, not arbitrary Racket inputs."""
    return self_check(grid)


# The functions below are explicitly WRONG rival rules, never label authorities.
def _render_rival(grid, components, hollow_mask, *, control=None, border_only=False):
    out = [list(row) for row in grid]
    selector = grid[0][0] if control is None else control
    out[0][0] = 0
    for cells, hollow in zip(components, hollow_mask):
        if (selector == 1) != hollow:
            continue
        r0, c0, r1, c1 = _bbox(cells)
        for r, c in cells:
            if not border_only or r in (r0, r1) or c in (c0, c1):
                out[r][c] = 8
    return out


def _rank_rival(grid, measure, extreme=min):
    components = _components7(grid)
    values = [measure(cells) for cells in components]
    threshold = extreme(values)
    return _render_rival(grid, components, [value != threshold for value in values])


def _not_smallest_area(grid):
    return _rank_rival(grid, len)


def _not_smallest_bbox_area(grid):
    return _rank_rival(grid, _bbox_area)


def _perimeter(cells):
    occupied = set(cells)
    return sum((r + dr, c + dc) not in occupied for r, c in cells
               for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def _not_smallest_perimeter(grid):
    return _rank_rival(grid, _perimeter)


def _not_lowest(grid):
    return _rank_rival(grid, lambda cells: _bbox(cells)[0], max)


def _not_rightmost(grid):
    return _rank_rival(grid, lambda cells: _bbox(cells)[1], max)


def _predicate_rival(grid, predicate):
    components = _components7(grid)
    return _render_rival(grid, components, [predicate(cells) for cells in components])


def _area_at_least_8(grid):
    return _predicate_rival(grid, lambda cells: len(cells) >= 8)


def _bbox_at_least_9(grid):
    return _predicate_rival(grid, lambda cells: _bbox_area(cells) >= 9)


def _height_at_least_3(grid):
    return _predicate_rival(grid, lambda cells: _bbox(cells)[2] - _bbox(cells)[0] >= 2)


def _width_at_least_3(grid):
    return _predicate_rival(grid, lambda cells: _bbox(cells)[3] - _bbox(cells)[1] >= 2)


def _square_pixel_count(grid):
    return _predicate_rival(grid, lambda cells: math.isqrt(len(cells)) ** 2 != len(cells))


def _border_only(grid):
    components = _components7(grid)
    return _render_rival(grid, components, [_is_hollow7(cells) for cells in components], border_only=True)


def _always_hollow(grid):
    components = _components7(grid)
    return _render_rival(grid, components, [_is_hollow7(cells) for cells in components], control=1)


def _always_solid(grid):
    components = _components7(grid)
    return _render_rival(grid, components, [_is_hollow7(cells) for cells in components], control=2)


def _branch_rival(grid, *, rival, control):
    """Wrong on one selector only; the other branch follows rectangle topology."""
    if grid[0][0] == control:
        return rival(grid)
    components = _components7(grid)
    return _render_rival(grid, components, [_is_hollow7(cells) for cells in components])


CANONICAL_SHORTCUTS = {
    "not_smallest_area": _not_smallest_area,
    "not_smallest_bbox_area": _not_smallest_bbox_area,
    "not_smallest_perimeter": _not_smallest_perimeter,
    "not_lowest": _not_lowest,
    "not_rightmost": _not_rightmost,
    "area_at_least_8": _area_at_least_8,
    "bbox_at_least_9": _bbox_at_least_9,
    "height_at_least_3": _height_at_least_3,
    "width_at_least_3": _width_at_least_3,
    "square_pixel_count": _square_pixel_count,
    "border_only": _border_only,
}
for _name, _rival in tuple(CANONICAL_SHORTCUTS.items()):
    for _control in (1, 2):
        if _name == "border_only" and _control == 1:
            # On frames, painting only the perimeter is the complete correct
            # answer. This would be an answer-equivalent rule on our domain.
            continue
        CANONICAL_SHORTCUTS[f"{_name}_only_control_{_control}"] = partial(
            _branch_rival, rival=_rival, control=_control)
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = {**CANONICAL_SHORTCUTS, "always_hollow": _always_hollow, "always_solid": _always_solid}


def _mixed_pair(grid, predicate):
    components = _components7(grid)
    return any(predicate(hollow, solid) for hollow in components if _is_hollow7(hollow)
               for solid in components if _is_solid7(solid))


def _size_reversal(grid):
    return _mixed_pair(grid, lambda hollow, solid: len(hollow) < len(solid))


def _equal_bbox(grid):
    return _mixed_pair(grid, lambda hollow, solid: _bbox_area(hollow) == _bbox_area(solid))


def _perimeter_contrast(grid):
    return _mixed_pair(grid, lambda hollow, solid: _perimeter(hollow) <= _perimeter(solid))


def _nonsquare_solid(grid):
    return any(_is_solid7(cells) and math.isqrt(len(cells)) ** 2 != len(cells)
               for cells in _components7(grid))


def _solid_interior(grid):
    return grid[0][0] == 2 and any(_is_solid7(cells) and
        _bbox(cells)[2] - _bbox(cells)[0] >= 2 and _bbox(cells)[3] - _bbox(cells)[1] >= 2
        for cells in _components7(grid))


def _teaching_contrast(grid, *, control):
    """Input geometry witnessing size, perimeter, position and threshold rivals."""
    if grid[0][0] != control:
        return False
    components = _components7(grid)
    for hollow in components:
        if not _is_hollow7(hollow) or _bbox_area(hollow) != 9:
            continue
        hr, hc, _, _ = _bbox(hollow)
        for solid in components:
            sr, sc, sr1, sc1 = _bbox(solid)
            if (_is_solid7(solid) and (sr1 - sr + 1, sc1 - sc + 1) in ((3, 5), (5, 3))
                    and hr >= sr and hc > sc):
                return True
    return False


SEMANTIC_WITNESSES = {
    "control_1": lambda grid: grid[0][0] == 1,
    "control_2": lambda grid: grid[0][0] == 2,
    "size_reversal": _size_reversal,
    "equal_bbox": _equal_bbox,
    "perimeter_contrast": _perimeter_contrast,
    "nonsquare_solid": _nonsquare_solid,
    "solid_interior": _solid_interior,
    "teaching_contrast_1": partial(_teaching_contrast, control=1),
    "teaching_contrast_2": partial(_teaching_contrast, control=2),
}
BRANCH_WITNESSES = ("control_1", "control_2")
WITNESS_RIVALS = {
    "size_reversal": ["not_smallest_area"],
    "equal_bbox": ["not_smallest_bbox_area"],
    "perimeter_contrast": ["not_smallest_perimeter"],
    "nonsquare_solid": ["square_pixel_count"],
    "solid_interior": ["border_only"],
}
for _control in (1, 2):
    WITNESS_RIVALS[f"teaching_contrast_{_control}"] = [
        name for name in CANONICAL_SHORTCUTS
        if ("_only_control_" not in name or name.endswith(f"_only_control_{_control}"))
        and not (_control == 1 and name == "border_only")
    ]


def lesson_identifiable(demos, query):
    """Finite declared-rival check using provided authoritative labels only."""
    return [f"{name} fits every demonstration but changes the query answer"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
