"""Nearest-Corner Dock inputs, bound to the unchanged canonical Racket rule.

One monochromatic 4-connected object moves rigidly to the nearest legal corner
placement. The center is the bounding-box center; exact ties choose top/left.
This module generates INPUTS ONLY. The Python oracle below is for diagnostic
contracts and rival probes; exported labels still come from canonical Racket.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "93e709ad4848"
TASK_ID = "93e709ad4848"
RULE_HASH = "684dd7c8349b"
VERSION = "3.0.0"
SUMMARY = (
    "One monochromatic 4-connected object on a zero background. Preserve its "
    "tight shape, holes, color and orientation while translating it to the "
    "nearest canvas corner, measured by bounding-box center. Equal distances "
    "choose top, then left. A three-profile teaching cycle distinguishes "
    "center/anchor rules, tie handling and independent canvas dimensions."
)
INVARIANTS = [
    "zero background and exactly one nonzero-color 4-connected object",
    "default inputs move visibly; canvas shape and all object pixels are preserved",
    "every consecutive three default draws cover boundary, tie and rectangular witnesses",
    "explicit overrides are exact; their domain guarantee does not imply the default lesson schedule",
]
AXES = {
    "grid_h": {"type": "int", "default": "profile-conditioned 8..24", "valid": "6..24"},
    "grid_w": {"type": "int", "default": "profile-conditioned 8..24", "valid": "6..24"},
    "object_color": {"type": "int", "default": "uniform 1..9", "valid": "1..9"},
    "shape_kind": {"type": "str", "default": "profile-conditioned shape family",
                   "valid": "ell|zigzag|hook|ring|rectangle"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("boundary", "tie", "rectangular")

_SHAPES = {
    "ell": ((0, 0), (1, 0), (1, 1)),
    "zigzag": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "hook": ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0)),
    "ring": tuple((r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)),
    "rectangle": tuple((r, c) for r in range(2) for c in range(3)),
}


def _normalize(cells):
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _variants(cells):
    variants = set()
    for transpose in (False, True):
        for row_sign in (-1, 1):
            for col_sign in (-1, 1):
                points = [(c, r) if transpose else (r, c) for r, c in cells]
                variants.add(_normalize([(row_sign*r, col_sign*c) for r, c in points]))
    return tuple(sorted(variants))


_SHAPE_VARIANTS = {name: _variants(cells) for name, cells in _SHAPES.items()}


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % SCHEDULE_PERIOD]


def _axis(ctx, name, defaults, legal):
    # Defaults may be stratified. Explicit overrides retain the complete declared
    # domain. Both paths record the actual returned value through the same key.
    options = legal if ctx.overrides.get(name) is not None else defaults
    return ctx.draw_choice(name, options)


def _geometry(grid):
    cells = [(r, c, v) for r, row in enumerate(grid)
             for c, v in enumerate(row) if v != 0]
    if not cells:
        raise ValueError("expected a nonempty object")
    r0 = min(r for r, c, v in cells)
    c0 = min(c for r, c, v in cells)
    sh = max(r for r, c, v in cells) - r0 + 1
    sw = max(c for r, c, v in cells) - c0 + 1
    return len(grid), len(grid[0]), r0, c0, sh, sw, cells


def _relocate(grid, bottom, right):
    h, w, r0, c0, sh, sw, cells = _geometry(grid)
    target_r = h - sh if bottom else 0
    target_c = w - sw if right else 0
    out = full_grid(h, w, 0)
    for r, c, color in cells:
        out[target_r + r - r0][target_c + c - c0] = color
    return out


def _semantic_oracle(grid):
    """Diagnostic bbox-margin oracle, never a substitute for Racket labels."""
    h, w, r0, c0, sh, sw, _ = _geometry(grid)
    return _relocate(grid, 2*r0 + sh > h, 2*c0 + sw > w)


def _render(h, w, cells, r0, c0, color):
    grid = full_grid(h, w, 0)
    for r, c in cells:
        grid[r0+r][c0+c] = color
    return grid


def _nonidentity_positions(h, w, sh, sw):
    return [(r, c) for r in range(h-sh+1) for c in range(w-sw+1)
            if r != (h-sh if 2*r+sh > h else 0)
            or c != (w-sw if 2*c+sw > w else 0)]


def _shape_for_profile(ctx, kind, profile):
    if profile == "boundary" and kind == "hook":
        # Top-heavy hook: on odd H, the bbox is below the center while the
        # occupied centroid ties it. Reflecting columns preserves that witness.
        options = [_normalize(_SHAPES[kind]),
                   _normalize([(r, -c) for r, c in _SHAPES[kind]])]
    elif profile == "tie" and kind == "ell":
        # Missing top-left corner: bbox ties TL, centroid and nearest pixel do not.
        options = [((0, 1), (1, 0), (1, 1))]
    elif profile == "tie" and kind == "hook":
        bottom_right = ((0, 2), (1, 2), (2, 2), (3, 0), (3, 1), (3, 2))
        options = [_normalize(bottom_right), _normalize([(c, r) for r, c in bottom_right])]
    else:
        options = _SHAPE_VARIANTS[kind]
    return ctx.draw_choice("object_orientation", options)


def _default_dimensions(ctx, profile, sh, sw, difficulty):
    if profile == "boundary":
        # Both profiles (9,9) and (9,11), palette-size 2, are canonical scales.
        return 9, ctx.draw_choice("boundary_width", (9, 11))
    if profile == "tie":
        # Equal parity makes the tight crop exactly centered. Keep substantial
        # canonical-scale support, while retaining larger ties in every band.
        row_options = [n for n in range(8, 25) if (n-sh) % 2 == 0]
        col_options = [n for n in range(8, 25) if (n-sw) % 2 == 0]
        row_options += [8 + sh % 2, 10 + sh % 2] * 8
        col_options += [8 + sw % 2, 10 + sw % 2] * 8
        return (ctx.draw_choice("tie_height", row_options),
                ctx.draw_choice("tie_width", col_options))
    pairs = [(8, 11), (8, 12), (9, 12), (9, 13), (10, 13), (10, 14)]
    if difficulty == "hard":
        pairs += [(10, 17), (11, 20), (12, 23)]
    elif difficulty == "medium" or difficulty is None:
        pairs += [(9, 15), (10, 16)]
    h, w = ctx.draw_choice("rectangular_size", pairs)
    return (w, h) if ctx.draw_choice("transpose_canvas", (False, True)) else (h, w)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name, value in overrides.items():
        if name in ("grid_h", "grid_w", "object_color"):
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer")
        elif type(value) is not str:
            raise ValueError(f"{name} must be a string")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    # Keep the rectangular shape family fixed within a seed's lesson stream.
    # Otherwise a ring can first appear in a query, leaving "fill all holes"
    # consistent with every demo. Positions, orientations and sizes still vary.
    rectangular_family = tuple(_SHAPES)[int(seed) % len(_SHAPES)]
    defaults = {"boundary": ("hook",), "tie": ("ell", "ell", "hook"),
                "rectangular": (rectangular_family,)}[profile]
    kind = _axis(ctx, "shape_kind", defaults, tuple(_SHAPES))
    cells = _shape_for_profile(ctx, kind, profile)
    sh, sw = max(r for r, c in cells)+1, max(c for r, c in cells)+1
    default_h, default_w = _default_dimensions(ctx, profile, sh, sw, difficulty)
    h = _axis(ctx, "grid_h", (default_h,), tuple(range(6, 25)))
    w = _axis(ctx, "grid_w", (default_w,), tuple(range(6, 25)))
    color = ctx.draw_int("object_color", 1, 9)
    positions = _nonidentity_positions(h, w, sh, sw)
    if profile == "boundary":
        desired_r = (h-sh)//2 + 1
        target_from_color = {7: (False, True), 4: (True, False),
                             8: (True, True), 6: (False, False)}.get(color, (False, False))
        preferred = [(r, c) for r, c in positions if r == desired_r
                     and 0 < c < w-sw
                     and (2*r+sh > h, 2*c+sw > w) != target_from_color]
    elif profile == "tie":
        preferred = [(r, c) for r, c in positions if 2*r+sh == h and 2*c+sw == w]
    else:
        preferred = []
        for r, c in positions:
            rr2, cc2 = 2*r+sh-1, 2*c+sw-1
            correct = (rr2 > h-1, cc2 > w-1)
            wrong_h = (rr2 > h-1, cc2 > h-1)
            wrong_w = (rr2 > w-1, cc2 > w-1)
            if correct != wrong_h and correct != wrong_w:
                preferred.append((r, c))
    # Exact caller controls can make a profile witness impossible (e.g. square
    # dimensions in a rectangular profile). They still produce a lawful moving
    # object, without clipping controls, dropping pixels or rejecting the draw.
    r0, c0 = ctx.draw_choice("object_position", preferred or positions)
    return _render(h, w, cells, r0, c0, color)


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    h, w = len(grid), len(grid[0])
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return ["grid dimensions must be in 1..30"]
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors in 0..9"]
    foreground = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    if not foreground:
        return ["expected one nonempty object"]
    if len(foreground) == h*w:
        return ["zero background must be present"]
    colors = {grid[r][c] for r, c in foreground}
    if len(colors) != 1:
        return ["the unique object must be monochromatic"]
    pending = [next(iter(foreground))]
    seen = set(pending)
    while pending:
        r, c = pending.pop()
        for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if point in foreground and point not in seen:
                seen.add(point)
                pending.append(point)
    return [] if seen == foreground else ["expected exactly one 4-connected component"]


def strict_canonical_like(grid):
    """Semantic domain, deliberately broader than the five generated masks."""
    return self_check(grid)


def observe_overrides(grid):
    h, w, _, _, _, _, cells = _geometry(grid)
    mask = _normalize([(r, c) for r, c, color in cells])
    names = [name for name, variants in _SHAPE_VARIANTS.items() if mask in variants]
    if len(names) != 1:
        raise ValueError("shape does not identify one advertised shape family")
    colors = {color for r, c, color in cells}
    if len(colors) != 1:
        raise ValueError("object is not monochromatic")
    return {"grid_h": h, "grid_w": w, "object_color": next(iter(colors)), "shape_kind": names[0]}


# All rivals are deliberately wrong rules, not label-generation alternatives.
def _top_left(grid):
    h, w, r, c, _, _, _ = _geometry(grid)
    return _relocate(grid, 2*r > h-1, 2*c > w-1)


def _bottom_right(grid):
    h, w, r, c, sh, sw, _ = _geometry(grid)
    return _relocate(grid, 2*(r+sh-1) > h-1, 2*(c+sw-1) > w-1)


def _centroid(grid):
    h, w, _, _, _, _, cells = _geometry(grid)
    n = len(cells)
    return _relocate(grid, 2*sum(r for r, c, v in cells) > n*(h-1),
                     2*sum(c for r, c, v in cells) > n*(w-1))


def _first_pixel(grid):
    h, w, _, _, _, _, cells = _geometry(grid)
    r, c, _ = cells[0]
    return _relocate(grid, 2*r > h-1, 2*c > w-1)


def _nearest_pixel(grid):
    h, w, _, _, _, _, cells = _geometry(grid)
    corners = ((0, 0), (0, w-1), (h-1, 0), (h-1, w-1))
    chosen = min(range(4), key=lambda k: min((r-corners[k][0])**2 + (c-corners[k][1])**2
                                           for r, c, v in cells))
    return _relocate(grid, chosen >= 2, chosen % 2 == 1)


def _half_cell(grid):
    h, w, r, c, sh, sw, _ = _geometry(grid)
    return _relocate(grid, 2*r+sh-1 > h, 2*c+sw-1 > w)


def _ties_bottom_right(grid):
    h, w, r, c, sh, sw, _ = _geometry(grid)
    return _relocate(grid, 2*r+sh >= h, 2*c+sw >= w)


def _height_for_both(grid):
    h, _, r, c, sh, sw, _ = _geometry(grid)
    return _relocate(grid, 2*r+sh > h, 2*c+sw > h)


def _width_for_both(grid):
    _, w, r, c, sh, sw, _ = _geometry(grid)
    return _relocate(grid, 2*r+sh > w, 2*c+sw > w)


def _color_lookup(grid):
    *_, cells = _geometry(grid)
    bottom, right = {7: (False, True), 4: (True, False),
                     8: (True, True), 6: (False, False)}.get(cells[0][2], (False, False))
    return _relocate(grid, bottom, right)


def _identity(grid):
    return [list(row) for row in grid]


def _always_top_left(grid):
    return _relocate(grid, False, False)


def _fill_enclosed_holes(grid):
    """RIVAL: rigidly dock, then incorrectly paint enclosed background cells."""
    out = _semantic_oracle(grid)
    h, w = len(out), len(out[0])
    color = next(v for row in out for v in row if v)
    pending = [(r, c) for r in range(h) for c in range(w)
               if (r in (0, h-1) or c in (0, w-1)) and out[r][c] == 0]
    outside = set(pending)
    while pending:
        r, c = pending.pop()
        for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if (0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0
                    and (rr, cc) not in outside):
                outside.add((rr, cc))
                pending.append((rr, cc))
    for r in range(h):
        for c in range(w):
            if out[r][c] == 0 and (r, c) not in outside:
                out[r][c] = color
    return out


CANONICAL_SHORTCUTS = {
    "bbox_top_left": _top_left,
    "bbox_bottom_right": _bottom_right,
    "occupied_centroid": _centroid,
    "first_pixel": _first_pixel,
    "nearest_foreground_pixel": _nearest_pixel,
    "half_cell_midpoint": _half_cell,
    "ties_bottom_right": _ties_bottom_right,
    "height_for_both_axes": _height_for_both,
    "width_for_both_axes": _width_for_both,
    "canonical_color_lookup": _color_lookup,
    "fill_enclosed_holes": _fill_enclosed_holes,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = {**CANONICAL_SHORTCUTS, "identity": _identity, "always_top_left": _always_top_left}


def _anchor_boundary(grid):
    h, w, r, c, sh, sw, _ = _geometry(grid)
    return ((2*r <= h-1 < 2*r+sh-1) or (2*c <= w-1 < 2*c+sw-1))


def _exact_tie(grid):
    h, w, r, c, sh, sw, _ = _geometry(grid)
    return (sh < h and 2*r+sh == h) or (sw < w and 2*c+sw == w)


def _independent_axes(grid):
    h, w, r, c, sh, sw, _ = _geometry(grid)
    rr2, cc2 = 2*r+sh-1, 2*c+sw-1
    return h != w and ((sh < h and min(h,w)-1 < rr2 <= max(h,w)-1)
                       or (sw < w and min(h,w)-1 < cc2 <= max(h,w)-1))


SEMANTIC_WITNESSES = {
    "bbox_crosses_anchor_midpoint": _anchor_boundary,
    "exact_tie_uses_top_left": _exact_tie,
    "rectangular_axis_thresholds": _independent_axes,
}
WITNESS_RIVALS = {
    "bbox_crosses_anchor_midpoint": ["bbox_top_left"],
    "exact_tie_uses_top_left": ["ties_bottom_right"],
    "rectangular_axis_thresholds": ["height_for_both_axes", "width_for_both_axes"],
}


def _counterexample_predicate(rival):
    """Expose observed disagreement; the gate checks it against Racket itself."""
    def witness(grid):
        return rival(grid) != _semantic_oracle(grid)
    return witness


# Bind every declared canonical shortcut, not just representative families.
# The independent reference gate falsifies a mistaken diagnostic oracle or
# an incorrect witness claim on the actual generated grid.
for _name, _rival in CANONICAL_SHORTCUTS.items():
    _witness_name = "counterexample_" + _name
    SEMANTIC_WITNESSES[_witness_name] = _counterexample_predicate(_rival)
    WITNESS_RIVALS[_witness_name] = [_name]


def lesson_identifiable(demos, query):
    """Finite-rival check; this does not claim universal rule identification."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"rival {name} fits every demo but disagrees on query")
    return reasons
