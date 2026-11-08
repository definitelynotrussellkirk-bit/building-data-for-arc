"""Anchored-lane palette swaps for d2acf2cb; labels remain canonical Racket.

Default lessons use a four-profile curriculum: rows/base, mixed/swapped,
columns/swapped, mixed/base. Any three of four consecutive profiles expose
both directions, both palette directions, and a once-swapped intersection.
The size cycle retains 60% canonical shapes, 20% long rectangles and 20%
30x30 grids. Joint semantic/size scheduling repeats every 20 sample indices.
Explicit overrides are authoring controls, outside this teaching guarantee.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "832404dc8a5c"
VERSION = "4.0.0"
TASK_ID = "832404dc8a5c"
RULE_HASH = "bce3d4596195"
SUMMARY = ("Dense 6-field with scattered 0s; interior rows/cols anchored by "
           "4-endpoints get {0<->8, 6<->7} swapped; 7/8 appear only inside "
           "lanes.")

# Rivals: 'output is input' refuted by any demo (lane cells always change).
# 'swap everywhere' refuted by every demo (non-lane cells untouched).
# 'swap only rows' refuted by cols-only demos (train[2], test[0]).
# '7/8 are part of the background texture' refuted by demos whose only 7/8
# cells sit inside lanes; outside lanes the field is pure {0,6}.
# 'one-directional 6->7, 0->8' refuted by swapped-style lanes whose 7s and
# 8s become 6s and 0s.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "cells use only {0, 4, 6, 7, 8}; the field outside lanes is pure {0, 6}",
    "4s appear only as complete endpoint pairs of interior anchored lanes",
    "values 7 and 8 appear only inside anchored lanes",
    "at least one anchored lane (except the no_anchors texture)",
    "lane interiors contain only {0, 6, 7, 8} (swap always visible)",
]

DEGENERATE_TEXTURES = ("no_anchors", "all_anchored", "single_anchor")
# Explicit override-only lawful endpoints of the same Racket rule. Lane-free
# examples retain a dense two-color field; sparse/monochrome impostors reject.
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
_LANE_PALETTES = ("mixed", "swapped", "base")
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_anchored_rows": 0, "n_anchored_cols": 0},
    {"texture": DEGENERATE_TEXTURES, "n_anchored_rows": None},
    {"texture": DEGENERATE_TEXTURES, "n_anchored_cols": None},
    {"texture": "no_anchors", "lane_palette": None},
]

AXES = {
    "grid_h":          {"type": "int", "default": "scheduled 6..30",
                        "valid": "6..30"},
    "grid_w":          {"type": "int", "default": "scheduled 8..30",
                        "valid": "8..30"},
    "n_anchored_rows": {"type": "int", "default": "band/mode 0..4",
                        "valid": "0..4"},
    "n_anchored_cols": {"type": "int", "default": "band/mode 0..4",
                        "valid": "0..4"},
    "zero_density":    {"type": "float", "default": "rng 0.35..0.55",
                        "valid": "0.1..0.7"},
    "lane_palette":    {"type": "str", "default": "mixed (balanced schedule)",
                        "valid": "|".join(_LANE_PALETTES)},
    "texture":         {"type": "str", "default": "none",
                        "valid": "none|" + "|".join(DEGENERATE_TEXTURES)},
}

_FIELD = (0, 6)           # outside-lane values
_LANE_VALUES = (0, 6, 7, 8)


# --------------------------------------------------------------------------
# Structural validation (input side only — outputs come from the Racket rule)
# --------------------------------------------------------------------------

def _lanes(grid):
    """(lane_rows, lane_cols): interior rows/cols with both endpoints 4."""
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(1, h - 1)
            if grid[r][0] == 4 and grid[r][w - 1] == 4]
    cols = [c for c in range(1, w - 1)
            if grid[0][c] == 4 and grid[h - 1][c] == 4]
    return rows, cols


def observe_overrides(grid):
    """Realized exact-axis values for the override contract: lane counts are
    directly observable from the drawn grid. (zero_density is a distribution
    parameter, not a per-grid exact value, so it is not reported.)"""
    lane_rows, lane_cols = _lanes(grid)
    return {"n_anchored_rows": len(lane_rows),
            "n_anchored_cols": len(lane_cols)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the explicit input grammar, including dense lane-free controls."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["invalid or empty row"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if not 6 <= h <= 30:
        errs.append(f"grid height {h} outside declared 6..30 envelope")
    if not 8 <= w <= 30:
        errs.append(f"grid width {w} outside declared 8..30 envelope")
    if any(type(v) is not int for row in grid for v in row):
        errs.append("grid cells must be integer colors, not booleans or coerced scalars")
    if errs:
        return errs
    bad = sorted({v for row in grid for v in row} - {0, 4, 6, 7, 8})
    if bad:
        errs.append(f"colors outside {{0,4,6,7,8}}: {bad}")
        return errs
    lane_rows, lane_cols = _lanes(grid)
    lane_r_set, lane_c_set = set(lane_rows), set(lane_cols)
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v == 4:
                endpoint = ((c in (0, w - 1) and r in lane_r_set)
                            or (r in (0, h - 1) and c in lane_c_set))
                if not endpoint:
                    errs.append(f"stray 4 at ({r},{c}) not part of a lane endpoint pair")
            elif v in (7, 8) and r not in lane_r_set and c not in lane_c_set:
                errs.append(f"value {v} at ({r},{c}) outside any anchored lane")
    if not lane_rows and not lane_cols:
        if any(v in (4, 7, 8) for row in grid for v in row):
            errs.append("lane-free grid must be a pure {0,6} field")
        minimum = max(6, (h * w + 9) // 10)
        if any(sum(row.count(value) for row in grid) < minimum for value in _FIELD):
            errs.append("lane-free control requires both field colors at density >= 10% (minimum 6 cells)")
    return errs


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; overrides validated against the full valid
    range (an override must execute on any band, per the AXES contract)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _draw_float(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Float analogue of _banded_int (fg densities)."""
    if label in overrides and overrides[label] is not None:
        v = float(overrides[label])
        if not valid_lo <= v <= valid_hi:
            raise ValueError(
                f"{label} override {v} outside [{valid_lo}, {valid_hi}]")
        return v
    return ctx.draw_rng(label).uniform(lo, hi)


def _fill_field(g, rng, zero_density):
    """Canonical field texture: every cell 6, or 0 with prob zero_density."""
    h, w = len(g), len(g[0])
    for r in range(h):
        for c in range(w):
            g[r][c] = 0 if rng.random() < zero_density else 6


def _paint_lane(g, rng, zero_density, style, r=None, c=None):
    """Mark one lane's 4-endpoints and style its interior. 'swapped' lanes
    hold pure 7/8 (canonical train[0]); 'base' lanes hold the field texture."""
    h, w = len(g), len(g[0])
    cells = ([(r, cc) for cc in range(1, w - 1)] if r is not None
             else [(rr, c) for rr in range(1, h - 1)])
    if r is not None:
        g[r][0] = g[r][w - 1] = 4
    else:
        g[0][c] = g[h - 1][c] = 4
    for rr, cc in cells:
        if g[rr][cc] == 4:
            continue  # keep an earlier lane's endpoint at intersections
        if style == "swapped":
            g[rr][cc] = rng.choice((7, 8))
        else:
            g[rr][cc] = 0 if rng.random() < zero_density else 6
    # A lane must teach both palette pairs, including on the smallest canvas.
    # Positions remain random; this does not encode the answer at a fixed cell.
    first, second = rng.sample(cells, 2)
    values = (7, 8) if style == "swapped" else (0, 6)
    for (rr, cc), value in zip((first, second), values):
        g[rr][cc] = value


def _lane_style(rng, lane_palette):
    if lane_palette in ("swapped", "base"):
        return lane_palette
    return rng.choice(("swapped", "base"))  # 'mixed': 50/50 per grid


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"Unknown override keys: {sorted(unknown)}")
    integer_bounds = {"grid_h": (6, 30), "grid_w": (8, 30),
                      "n_anchored_rows": (0, 4), "n_anchored_cols": (0, 4)}
    for name, (lo, hi) in integer_bounds.items():
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    value = overrides.get("zero_density")
    if value is not None and (type(value) not in (int, float) or not math.isfinite(value)
                              or not 0.1 <= value <= 0.7):
        raise ValueError("zero_density must be a finite number in 0.1..0.7")
    for name, choices in (("lane_palette", _LANE_PALETTES),
                          ("texture", ("none",) + DEGENERATE_TEXTURES)):
        value = overrides.get(name)
        if value is not None and (not isinstance(value, str) or value not in choices):
            raise ValueError(f"{name} must be one of {choices}")


def _default_shape(ctx, sample_index, style):
    rng = ctx.draw_rng("size_schedule")
    size_phase = sample_index % 5
    if size_phase < 3:
        return (9 if style == "swapped" else rng.choice((6, 7, 10))), 9
    if size_phase == 4:
        return 30, 30
    if rng.randrange(2):
        return rng.randint(21, 29), rng.randint(8, 20)
    return rng.randint(6, 20), rng.randint(21, 29)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    band = difficulty or "medium"
    lanes_lo, lanes_hi = {"easy": (1, 1), "medium": (1, 3), "hard": (2, 4)}[band]
    mode, scheduled_style = _TEACHING_PROFILES[sample_index % 4]
    lane_palette = overrides.get("lane_palette") or "mixed"
    style = scheduled_style if lane_palette == "mixed" else lane_palette
    default_h, default_w = _default_shape(ctx, sample_index, style)
    h = _banded_int(ctx, overrides, "grid_h", default_h, default_h, 6, 30)
    w = _banded_int(ctx, overrides, "grid_w", default_w, default_w, 8, 30)
    zero_density = _draw_float(ctx, overrides, "zero_density",
                               0.35, 0.55, 0.1, 0.7)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")

    rows_over = "n_anchored_rows" in overrides and overrides["n_anchored_rows"] is not None
    cols_over = "n_anchored_cols" in overrides and overrides["n_anchored_cols"] is not None
    palette_over = "lane_palette" in overrides and overrides["lane_palette"] is not None
    if texture in DEGENERATE_TEXTURES:
        if rows_over or cols_over:
            raise ValueError(
                f"texture={texture!r} fixes the anchor layout; "
                "n_anchored_rows/n_anchored_cols overrides are incompatible")
        if texture == "no_anchors" and palette_over:
            raise ValueError(
                "texture='no_anchors' has no lanes to style; "
                "lane_palette is incompatible")
        return _draw_from_degenerate(texture, h, w, rng, zero_density, style)
    n_arows = int(overrides["n_anchored_rows"]) if rows_over else None
    n_acols = int(overrides["n_anchored_cols"]) if cols_over else None
    if rows_over and cols_over and n_arows == 0 and n_acols == 0:
        raise ValueError(
            "n_anchored_rows=0 and n_anchored_cols=0 leaves no anchored "
            "lane; use texture='no_anchors' for a lane-free grid")

    g = full_grid(h, w, 0)
    _fill_field(g, rng, zero_density)
    if not rows_over and not cols_over:
        if mode == "rows":
            n_arows, n_acols = rng.randint(lanes_lo, lanes_hi), 0
        elif mode == "cols":
            n_arows, n_acols = 0, rng.randint(lanes_lo, lanes_hi)
        else:
            n_arows = rng.randint(1, max(1, lanes_hi // 2))
            n_acols = rng.randint(1, max(1, lanes_hi // 2))
    lane_rows, lane_cols = _plan_lanes(
        rng, h, w, n_arows, n_acols, lanes_lo, lanes_hi, 0.0)
    # KRF-0004 provenance: record the REALIZED lane counts under their
    # declared labels (raw-RNG selection inside _plan_lanes; these values are
    # final and equal to observe_overrides on the returned grid).
    ctx.overrides["n_anchored_rows"] = len(lane_rows)
    ctx.draw_int("n_anchored_rows", 0, 4)
    ctx.overrides["n_anchored_cols"] = len(lane_cols)
    ctx.draw_int("n_anchored_cols", 0, 4)
    for r in lane_rows:
        _paint_lane(g, rng, zero_density, style, r=r)
    for c in lane_cols:
        _paint_lane(g, rng, zero_density, style, c=c)
    return g


def _plan_lanes(rng, h, w, n_arows, n_acols, lanes_lo, lanes_hi, mixed_p):
    """Choose lane rows/cols. Canonical never mixes rows+cols; the hard band
    may (mixed_p). Explicit counts (non-None) pin that side."""
    interior_rows = list(range(1, h - 1))
    interior_cols = list(range(1, w - 1))
    if n_arows is None and n_acols is None:
        total = rng.randint(lanes_lo, lanes_hi)
        mode = "mixed" if rng.random() < mixed_p else rng.choice(("rows", "cols"))
        if mode == "rows":
            n_arows, n_acols = total, 0
        elif mode == "cols":
            n_arows, n_acols = 0, total
        else:
            n_arows = rng.randint(1, total - 1) if total > 1 else 1
            n_acols = total - n_arows
    elif n_arows is None:
        n_arows = max(1, lanes_lo - n_acols) if n_acols == 0 else 0
    elif n_acols is None:
        n_acols = max(1, lanes_lo - n_arows) if n_arows == 0 else 0
    n_arows = min(n_arows, len(interior_rows))
    n_acols = min(n_acols, len(interior_cols))
    lane_rows = rng.sample(interior_rows, n_arows) if n_arows else []
    lane_cols = rng.sample(interior_cols, n_acols) if n_acols else []
    return lane_rows, lane_cols


def _draw_from_degenerate(name, h, w, rng, zero_density, style):
    g = full_grid(h, w, 0)
    _fill_field(g, rng, zero_density)
    if name == "all_anchored":
        for r in range(1, h - 1):
            _paint_lane(g, rng, zero_density, style, r=r)
    elif name == "single_anchor":
        _paint_lane(g, rng, zero_density, style, r=h // 2)
    else:
        # Preserve the documented dense field, excluding sparse identity
        # impostors while keeping the explicit no-lanes control lawful.
        minimum = max(6, (h * w + 9) // 10)
        for value in _FIELD:
            present = sum(row.count(value) for row in g)
            if present < minimum:
                candidates = [(r, c) for r in range(h) for c in range(w)
                              if g[r][c] != value]
                for r, c in rng.sample(candidates, minimum - present):
                    g[r][c] = value
    # no_anchors: pure field, rule is the identity on it
    return g


_TEACHING_PROFILES = (("rows", "base"), ("mixed", "swapped"),
                      ("cols", "swapped"), ("mixed", "base"))
LESSON_SCHEDULE_PERIOD = 20
SCHEDULE_PROFILES = tuple(f"{mode}/{style}/size{size}" for mode, style in _TEACHING_PROFILES
                          for size in range(5))


def schedule_profile(seed, sample_index, difficulty=None):
    mode, style = _TEACHING_PROFILES[sample_index % 4]
    return f"{mode}/{style}/size{sample_index % 5}"


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    rows, cols = _lanes(grid)
    h, w = len(grid), len(grid[0])
    if w != 9 or h not in (6, 7, 9, 10):
        return ["outside canonical size anchors"]
    if bool(rows) == bool(cols) or not 1 <= len(rows) + len(cols) <= 3:
        return ["canonical examples have one orientation and one to three lanes"]
    return []


def _predict_rival(grid, kind):
    rows, cols = map(set, _lanes(grid))
    swap = {0: 8, 8: 0, 6: 7, 7: 6}
    if kind == "forward_only":
        swap = {0: 8, 6: 7}
    elif kind == "reverse_only":
        swap = {8: 0, 7: 6}
    result = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            active = r in rows or c in cols
            if kind == "rows_only":
                active = r in rows
            elif kind == "columns_only":
                active = c in cols
            elif kind == "identity":
                active = False
            elif kind == "swap_everywhere":
                active = True
            elif kind == "double_swap_intersections":
                active = (r in rows) != (c in cols)
            if active:
                result[r][c] = swap.get(value, value)
    return result


def _rival(kind):
    def solve(grid):
        return _predict_rival(grid, kind)
    return solve


LESSON_COMPETITORS = {name: _rival(name) for name in (
    "identity", "swap_everywhere", "rows_only", "columns_only",
    "forward_only", "reverse_only", "double_swap_intersections")}
CANONICAL_SHORTCUTS = {
    "double_swap_intersections": LESSON_COMPETITORS["double_swap_intersections"]}
SEMANTIC_RIVALS = LESSON_COMPETITORS


def _has_mixed(grid):
    rows, cols = _lanes(grid)
    return bool(rows and cols)


def _has_base_lane(grid):
    rows, cols = map(set, _lanes(grid))
    return any(v in (0, 6) and (r in rows or c in cols)
               for r, row in enumerate(grid) for c, v in enumerate(row))


def _has_swapped_lane(grid):
    return any(v in (7, 8) for row in grid for v in row)


SEMANTIC_WITNESSES = {"mixed_intersection": _has_mixed,
                      "base_palette": _has_base_lane,
                      "swapped_palette": _has_swapped_lane}
WITNESS_RIVALS = {"mixed_intersection": ["double_swap_intersections"],
                  "base_palette": ["reverse_only"],
                  "swapped_palette": ["forward_only"]}


def lesson_identifiable(demos, query):
    """Finite declared-rival check, not uniqueness over arbitrary programs."""
    if not demos:
        return ["at least one labeled demonstration is required"]
    reasons = []
    for name, solve in LESSON_COMPETITORS.items():
        if all(solve(pair["input"]) == pair["output"] for pair in demos):
            if solve(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
