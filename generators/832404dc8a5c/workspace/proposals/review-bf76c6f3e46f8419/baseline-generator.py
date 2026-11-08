"""Generator for d2acf2cb.

Rule: every cell whose row is 4-anchored (col 0 == col w-1 == 4) or whose
column is 4-anchored (row 0 == row h-1 == 4) is palette-swapped:
0<->8 and 6<->7.  Anchors (4s) and all non-lane cells are unchanged.

Canonical texture (measured on all 4 pairs): a dense field of 6s with 0s
scattered at p ~= 0.44..0.55; values 7 and 8 appear ONLY inside anchored
lanes; lanes are rows-only (2 pairs) or columns-only (2 pairs), 1..3 lanes,
always at interior rows/columns; grid is always w=9, h 6..10.  Lanes come in
two styles: 'swapped' lanes filled with 7s and 8s (train[0]) and 'base'
lanes holding the same 0/6 texture as the field (train[1], train[2],
test[0]).

Combinatorial axes (7): grid_h, grid_w, n_anchored_rows, n_anchored_cols,
zero_density, lane_palette, texture.  Anchor mode (rows-only / cols-only /
mixed) is an internal weighted draw (canonical never mixes); hard band
allows the mixed extension.  Degenerate textures (no_anchors, all_anchored,
single_anchor) are crash-free identity/extreme cases that reject the
lane-count and lane-style overrides they cannot honor.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "832404dc8a5c"
VERSION = "3.0.0"  # canonical texture (6-field) + cols-only mode + self_check + RULE_HASH
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
_LANE_PALETTES = ("mixed", "swapped", "base")

AXES = {
    "grid_h":          {"type": "int", "default": "band rng 6..13",
                        "valid": "6..13"},
    "grid_w":          {"type": "int", "default": "band rng 8..12",
                        "valid": "8..12"},
    "n_anchored_rows": {"type": "int", "default": "band/mode 0..4",
                        "valid": "0..4"},
    "n_anchored_cols": {"type": "int", "default": "band/mode 0..4",
                        "valid": "0..4"},
    "zero_density":    {"type": "float", "default": "rng 0.35..0.55",
                        "valid": "0.1..0.7"},
    "lane_palette":    {"type": "str", "default": "mixed (50/50 per grid)",
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
    """Structural invariants of a lawful instance (all four canonical pairs
    satisfy them): rectangular grid over {0,4,6,7,8} inside the declared
    6..13 x 8..12 envelope; every 4 belongs to the endpoint pair of an
    interior anchored row or column (no lone 4s, no corner 4s, no edge
    lanes); values 7/8 appear only inside anchored lanes; a lane-free grid
    (the no_anchors texture) holds a pure {0,6} field.
    Rejects out-of-envelope canvases (e.g. a 5x8 all-zero grid), scattered
    4s (would create accidental/mismarked lanes), 7/8 in the field, and
    foreign colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    # Declared envelope (AXES): grid_h in 6..13, grid_w in 8..12. A canvas
    # outside it is not a lawful instance of this generator's family, even
    # when it is otherwise structurally clean (e.g. a 5x8 all-zero grid).
    if not 6 <= h <= 13:
        errs.append(f"grid height {h} outside declared 6..13 envelope")
    if not 8 <= w <= 12:
        errs.append(f"grid width {w} outside declared 8..12 envelope")
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


def _lane_style(rng, lane_palette):
    if lane_palette in ("swapped", "base"):
        return lane_palette
    return rng.choice(("swapped", "base"))  # 'mixed': 50/50 per grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, w_lo, w_hi, lanes_lo, lanes_hi, mixed_p = 6, 8, 8, 9, 1, 1, 0.0
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi, lanes_lo, lanes_hi, mixed_p = 9, 13, 9, 12, 2, 4, 0.3
    else:
        h_lo, h_hi, w_lo, w_hi, lanes_lo, lanes_hi, mixed_p = 7, 10, 9, 10, 1, 3, 0.0
    h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, 6, 13)
    w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, 8, 12)
    zero_density = _draw_float(ctx, overrides, "zero_density",
                               0.35, 0.55, 0.1, 0.7)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    lane_palette = overrides.get("lane_palette") or "mixed"

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
        return _draw_from_degenerate(texture, h, w, rng, zero_density,
                                     _lane_style(rng, lane_palette))
    n_arows = int(overrides["n_anchored_rows"]) if rows_over else None
    n_acols = int(overrides["n_anchored_cols"]) if cols_over else None
    if rows_over and cols_over and n_arows == 0 and n_acols == 0:
        raise ValueError(
            "n_anchored_rows=0 and n_anchored_cols=0 leaves no anchored "
            "lane; use texture='no_anchors' for a lane-free grid")

    g = full_grid(h, w, 0)
    _fill_field(g, rng, zero_density)
    style = _lane_style(rng, lane_palette)
    lane_rows, lane_cols = _plan_lanes(
        rng, h, w, n_arows, n_acols, lanes_lo, lanes_hi, mixed_p)
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
    # no_anchors: pure field, rule is the identity on it
    return g
