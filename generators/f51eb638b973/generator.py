"""Generator for puzzle e179c5f4.

Rule: the input is a 0-background grid with exactly one blue(1) cell on the
bottom row.  A ball launched from that cell travels upward on a diagonal —
initially up-right when the cell sits in column 0, otherwise up-left —
reversing horizontal direction at each left/right wall until it exits the
top edge.  Output: every path cell becomes 1, every other cell becomes 8.

Canonical pairs always start in the bottom-LEFT corner (column 0) on 10x2..5
grids; the oracle defines the bounce for any start column, so the generator
varies the start column across the full width.  That variation is also the
anti-shortcut witness: with a fixed corner start the whole output would be
predictable from dimensions alone.

Combinatorial axes (5): grid_h/w, blue_col_position, position_bias, texture.
Degenerate textures (no_blue / multiple_blues / blue_top_row) were removed:
they produced rule-invalid inputs the per-puzzle contract forbids (every
returned grid must stay oracle-valid and pass self_check).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f51eb638b973"
VERSION = "3.1.0"  # distribution break over 3.0.0: explicit canonical prior
# (30% of default draws on every band land on h=10, w 2..5, left-corner
# start) per the KRF-0003 semantic veto; generalized witnesses retained.
# 3.0.0 was: band ranges inside declared valid ranges, removed dead axes and
# rule-breaking degenerate textures, added structural self_check + RULE_HASH.
TASK_ID = "f51eb638b973"
RULE_HASH = "160e5c81f22f"
SUMMARY = (
    "0-bg grid with EXACTLY ONE blue(1) cell on the BOTTOM ROW. "
    "Rule: launch a ball from the blue cell upward on a diagonal "
    "(up-right from column 0, up-left otherwise), bouncing off the "
    "left/right walls until it exits the top edge. Paint every path "
    "cell 1 and every other cell 8."
)

INVARIANTS = [
    "background is 0",
    "exactly one blue(1) cell",
    "blue cell is on the bottom row of the grid",
    "palette is only 0 plus the single blue cell (no color 8 in input; "
    "the rule writes 8 for non-path cells)",
    "width >= 2 (the bounce oracle needs both a left and a right wall)",
]

POSITION_BIAS = ("center", "left_edge", "right_edge", "spread")
# Default draw mix: "spread" (uniform column) weighted 4:1 over each pinned
# bias so start columns stay near-uniform while every bias keeps positive
# witnesses (a fixed-corner start would make the output dimension-predictable).
_BIAS_DRAW_MIX = ("spread", "spread", "spread", "spread",
                  "center", "left_edge", "right_edge")
# Canonical prior (KRF-0003 veto fix): on default draws (no shape override),
# every band lands on the exact empirical canonical family (h=10, w in 2..5,
# left-corner start) with this probability; the remaining draws keep the
# generalized band envelopes as anti-shortcut witnesses.  0.30 keeps the
# pooled joint canonical-like rate >=0.25 while per-band distinctness stays
# well above the 70% bar (0.35 would push diversity toward the floor).
_CANONICAL_PRIOR_P = 0.30
DEGENERATE_TEXTURES: tuple = ()
HELPFUL_TEXTURES = POSITION_BIAS

_H_LO, _H_HI = 4, 18
_W_LO, _W_HI = 2, 18

AXES = {
    "grid_h":            {"type": "int", "default": "band rng 4..9 easy, "
                              "8..16 medium, 12..18 hard; 30% of default "
                              "draws pin the canonical h=10",
                          "valid": "4..18"},
    "grid_w":            {"type": "int", "default": "band rng 2..8 easy, "
                              "2..12 medium, 5..14 hard; 30% of default "
                              "draws pin the canonical w=2..5",
                          "valid": "2..18"},
    "blue_col_position": {"type": "int", "default": "rng 0..w-1 or pinned by "
                              "position_bias; column 0 on canonical-prior "
                              "draws", "valid": "0..w-1"},
    "position_bias":     {"type": "str", "default": "rng helpful",
                          "valid": "|".join(POSITION_BIAS)},
    "texture":           {"type": "str", "default": "alias for position_bias",
                          "valid": "|".join(HELPFUL_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared valid range, colors 0..9, palette restricted to 0 plus
    exactly one blue(1) cell, and that blue cell on the bottom row.  Band
    ranges are defaults only, so difficulty is deliberately unused."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for row in grid for v in row):
        errs.append("color outside 0..9")
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errs.append(f"dims {h}x{w} outside valid "
                    f"{_H_LO}..{_H_HI} x {_W_LO}..{_W_HI}")
    flat = [v for row in grid for v in row]
    n_blue = flat.count(1)
    if n_blue != 1:
        errs.append(f"expected exactly one blue(1) cell, found {n_blue}")
    if any(v == 8 for v in flat):
        errs.append("color 8 in input (the rule writes 8 for non-path cells)")
    if any(v not in (0, 1) for v in flat):
        errs.append("palette must be 0 background plus the single blue cell")
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 1 and r != h - 1:
                errs.append(f"blue cell at row {r}, not the bottom row")
    return errs


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an explicit override is validated against the
    full declared valid range (overrides are band-independent, KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _bias_column(bias, w, rng):
    if bias == "center":
        return w // 2
    if bias == "left_edge":
        return 0
    if bias == "right_edge":
        return w - 1
    return rng.randint(0, w - 1)


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0002): the
    blue start column actually painted on the bottom row, derived from the
    returned grid itself, never from request metadata."""
    col = None
    if grid and grid[-1]:
        for c, v in enumerate(grid[-1]):
            if v == 1:
                col = c
                break
    return {"blue_col_position": col}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, w_lo, w_hi = 4, 9, 2, 8
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi = 12, 18, 5, 14
    else:
        h_lo, h_hi, w_lo, w_hi = 8, 16, 2, 12

    texture = overrides.get("texture")
    if texture is not None and texture not in POSITION_BIAS:
        raise ValueError(
            f"unknown texture {texture!r}; valid: {POSITION_BIAS}")
    if texture is not None and overrides.get("position_bias") is not None:
        raise ValueError("texture and position_bias are conflicting aliases; "
                         "pass only one")
    explicit_bias = texture or overrides.get("position_bias")

    col_override = overrides.get("blue_col_position")
    if col_override is not None:
        col_override = int(col_override)
        if col_override < 0:
            raise ValueError(f"blue_col_position {col_override} below 0")
        if col_override > _W_HI - 1:
            raise ValueError(f"blue_col_position {col_override} needs width "
                             f">= {col_override + 1}, beyond valid max {_W_HI}")
        # The free width axis may grow to host the requested column; an
        # explicitly overridden width may not be exceeded.
        if overrides.get("grid_w") is None:
            w_lo = max(w_lo, col_override + 1)
            w_hi = max(w_hi, w_lo)

    # Canonical prior (KRF-0003): default draws (no shape override) land on
    # the exact canonical family with probability _CANONICAL_PRIOR_P.  Any
    # explicit shape override bypasses the prior and stays exact.
    shape_override = any(
        overrides.get(k) is not None
        for k in ("grid_h", "grid_w", "blue_col_position",
                  "position_bias", "texture"))
    canonical_draw = not shape_override and rng.random() < _CANONICAL_PRIOR_P
    if canonical_draw:
        h_lo = h_hi = 10
        w_lo, w_hi = 2, 5

    h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, _H_LO, _H_HI)
    w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, _W_LO, _W_HI)

    if col_override is not None:
        # Only an explicitly requested fixed bias can conflict with an
        # explicit column ("spread" stays compatible with any column).
        if explicit_bias in ("center", "left_edge", "right_edge"):
            implied = _bias_column(explicit_bias, w, rng)
            if implied != col_override:
                raise ValueError(
                    f"blue_col_position {col_override} conflicts with "
                    f"position_bias {explicit_bias!r} (column {implied})")
        sc = ctx.draw_int("blue_col_position", 0, w - 1)
    elif canonical_draw:
        sc = 0
    else:
        pos_bias = explicit_bias or \
            ctx.draw_choice("position_bias", list(_BIAS_DRAW_MIX))
        sc = _bias_column(pos_bias, w, rng)

    g = full_grid(h, w, 0)
    g[h - 1][sc] = 1
    return g
