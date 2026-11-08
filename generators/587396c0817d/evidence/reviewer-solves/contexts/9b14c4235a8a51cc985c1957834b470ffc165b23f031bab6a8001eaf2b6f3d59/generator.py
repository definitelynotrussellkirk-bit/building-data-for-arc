"""Generator for 2a28add5.

Rule (per row, independently): let non7 be the columns of the non-7 cells in
column order.  If the row contains a color-6 (magenta) anchor among them,
paint a color-8 bar whose length equals the number of non-7 cells and whose
offset places the bar start at c6 - idx, where idx is the number of non-7
cells left of the 6 (the 6's column-rank).  Rows without a 6 become all 7;
every other cell becomes 7.

Canonical 10x10 inputs are DENSE: 4-6 rows carry a 6-anchored bar pattern,
3-5 further rows carry 1-6 decoy non-7 cells (which trigger NO bar), and
color 8 may already appear as a decoy.  The generator reproduces that
active/decoy/empty row mix so "row has non-7 cells" is not a shortcut for
"row gets a bar".

Combinatorial axes (7): grid_h/w, n_active_rows, n_decoy_rows,
bar_length_kind, idx_kind, palette_kind, texture (alias for
bar_length_kind).  The old degenerate textures (no_active_rows / all_six /
multiple_sixes) were removed: they violate the one-anchor-per-row contract
the per-puzzle self_check must enforce.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "587396c0817d"
VERSION = "3.1.0"  # distribution break over 3.0.0: explicit 80% canonical
# prior on the default band (10x10, 4..5 active + 4..5 decoy rows), bars
# lifted to the canonical 7-cell extreme under an exact plurality budget.
# 3.0.0 was: dense canonical-style rows (decoy rows without a 6, color-8
# decoys allowed), removed dead axes and rule-breaking degenerate textures,
# added n_decoy_rows, structural self_check, observe_overrides, RULE_HASH.
TASK_ID = "587396c0817d"
RULE_HASH = "703072e0ab28"
SUMMARY = (
    "7-bg grid whose rows mix three kinds: ACTIVE rows with exactly one "
    "color-6 anchor plus other non-7 cells, DECOY rows with non-7 cells "
    "but no 6, and EMPTY all-7 rows. Rule: per row, if a 6 is present "
    "among the non-7 cells, paint an 8-bar whose length is the non-7 "
    "count, starting at c6 - idx where idx is the 6's column-rank among "
    "the non-7 cells; everything else becomes 7."
)

INVARIANTS = [
    "7 is the modal color",
    "every row contains at most one color-6 cell",
    "a row with a 6 carries at least 3 non-7 cells (anchor + decoys)",
    "at least one row contains a 6 (the rule fires on every instance)",
    "rows without a 6 may hold 1+ decoy non-7 cells of any non-6 color "
    "(including 8; the rule repaints the whole grid 7/8)",
    "grid dims stay within 6..18 x 8..20",
]

BAR_LENGTH_KINDS = ("small", "medium", "large", "varied")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
IDX_KINDS = ("spread", "left_biased", "right_biased")
DEGENERATE_TEXTURES: tuple = ()
HELPFUL_TEXTURES = BAR_LENGTH_KINDS

_H_LO, _H_HI = 6, 18
_W_LO, _W_HI = 8, 20
_ACTIVE_LO, _ACTIVE_HI = 1, 6
_DECOY_LO, _DECOY_HI = 0, 5

AXES = {
    "grid_h":          {"type": "int", "default": "band rng 6..9 easy, "
                            "9..11 medium (80% canonical-prior draws pin "
                            "10x10), 12..18 hard",
                        "valid": "6..18"},
    "grid_w":          {"type": "int", "default": "band rng 8..11 easy, "
                            "9..11 medium (80% canonical-prior draws pin "
                            "10x10), 14..20 hard",
                        "valid": "8..20"},
    "n_active_rows":   {"type": "int", "default": "band rng 1..3 easy, "
                            "3..5 medium (4..5 under the canonical prior), "
                            "4..6 hard", "valid": "1..6"},
    "n_decoy_rows":    {"type": "int", "default": "band rng 1..3 easy, "
                            "3..5 medium (4..5 under the canonical prior), "
                            "3..5 hard", "valid": "0..5"},
    "bar_length_kind": {"type": "str", "default": "rng helpful",
                        "valid": "|".join(BAR_LENGTH_KINDS)},
    "idx_kind":        {"type": "str", "default": "rng spread|left_biased|"
                            "right_biased", "valid": "|".join(IDX_KINDS)},
    "palette_kind":    {"type": "str", "default": "rng helpful",
                        "valid": "|".join(PALETTE_KINDS)},
    "texture":         {"type": "str", "default": "alias for bar_length_kind",
                        "valid": "|".join(HELPFUL_TEXTURES)},
}

_PALETTES = {
    "warm": [2, 3, 4, 9],
    "cool": [1, 5, 8],
    "small": [0, 1, 2],
    "broad": [0, 1, 2, 3, 4, 5, 8, 9],
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared valid range, colors 0..9, 7 strictly modal, at most one
    color-6 anchor per row, every 6-row carries at least 3 non-7 cells, and
    at least one 6-row exists.  Band ranges are defaults only, so difficulty
    is deliberately unused."""
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
    freq = {}
    for row in grid:
        for v in row:
            freq[v] = freq.get(v, 0) + 1
    others = max((n for c, n in freq.items() if c != 7), default=0)
    if freq.get(7, 0) <= others:
        errs.append("background 7 is not the modal color")
    n_active = 0
    for r in range(h):
        row = grid[r]
        sixes = row.count(6)
        if sixes > 1:
            errs.append(f"row {r} has {sixes} color-6 anchors (max one)")
        non7 = sum(1 for v in row if v != 7)
        if sixes == 1:
            n_active += 1
            if non7 < 3:
                errs.append(f"row {r} has a 6 but only {non7} non-7 cells "
                            f"(need >=3)")
    if n_active == 0:
        errs.append("no active row: no row contains a color-6 anchor")
    return errs


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0002),
    derived from the returned grid itself: rows containing a color-6 anchor
    (active) and rows with non-7 cells but no 6 (decoy)."""
    n_active = 0
    n_decoy = 0
    for row in grid or []:
        non7 = sum(1 for v in row if v != 7)
        if 6 in row:
            n_active += 1
        elif non7 > 0:
            n_decoy += 1
    return {"n_active_rows": n_active, "n_decoy_rows": n_decoy}


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an explicit override is validated against the
    full declared valid range (overrides are band-independent, KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _bar_length(kind, w, rng):
    if kind == "small":
        return rng.randint(3, min(4, w))
    if kind == "medium":
        return rng.randint(4, min(6, w))
    if kind == "large":
        return rng.randint(6, min(8, w))
    return rng.randint(3, min(8, w))


def _draw_idx(kind, bar_len, rng):
    if kind == "left_biased":
        return rng.randint(0, max(0, bar_len // 3))
    if kind == "right_biased":
        return rng.randint(max(0, 2 * bar_len // 3), bar_len - 1)
    return rng.randint(0, bar_len - 1)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 9, 8, 11
        a_lo, a_hi, d_lo, d_hi = 1, 3, 1, 3
        decoy_cells = (1, 3)
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi = 12, 18, 14, 20
        a_lo, a_hi, d_lo, d_hi = 4, 6, 3, 5
        decoy_cells = (2, 6)
    else:
        # Medium carries an explicit canonical prior (KRF-0003): 80% of
        # default draws land exactly on the empirical manifold (10x10 with
        # 4..5 active and 4..5 decoy rows, like every official pair); the
        # remaining draws keep the generalized 9..11 square envelope with
        # 3..5 rows of each role.  Overrides always bypass the prior (the
        # full declared ranges stay reachable and exact).
        h_lo, h_hi, w_lo, w_hi = 9, 11, 9, 11
        a_lo, a_hi, d_lo, d_hi = 3, 5, 3, 5
        decoy_cells = (2, 5)
        if rng.random() < 0.8:
            h_lo = h_hi = w_lo = w_hi = 10
            a_lo, a_hi, d_lo, d_hi = 4, 5, 4, 5

    texture = overrides.get("texture")
    if texture is not None and texture not in BAR_LENGTH_KINDS:
        raise ValueError(
            f"unknown texture {texture!r}; valid: {BAR_LENGTH_KINDS}")
    if texture is not None and overrides.get("bar_length_kind") is not None:
        raise ValueError("texture and bar_length_kind are conflicting "
                         "aliases; pass only one")
    bar_kind = texture or overrides.get("bar_length_kind") or \
        ctx.draw_choice("bar_length_kind", list(BAR_LENGTH_KINDS))
    palette_kind = overrides.get("palette_kind") or \
        ctx.draw_choice("palette_kind", list(PALETTE_KINDS))
    idx_kind = overrides.get("idx_kind") or \
        ctx.draw_choice("idx_kind", list(IDX_KINDS))
    palette = _PALETTES[palette_kind]

    h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, _H_LO, _H_HI)
    w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, _W_LO, _W_HI)

    # Row-count contract: exact when overridden; the free count adapts so
    # active + decoy never exceeds the canvas.  Both-explicit overflow is a
    # loud rejection, never a silent truncation.
    a_override = overrides.get("n_active_rows") is not None
    d_override = overrides.get("n_decoy_rows") is not None
    if a_override and d_override:
        n_active = ctx.draw_int("n_active_rows", _ACTIVE_LO, _ACTIVE_HI)
        n_decoy = ctx.draw_int("n_decoy_rows", _DECOY_LO, _DECOY_HI)
        if n_active + n_decoy > h:
            raise ValueError(
                f"n_active_rows={n_active} + n_decoy_rows={n_decoy} exceeds "
                f"grid_h={h}")
    elif a_override:
        n_active = ctx.draw_int("n_active_rows", _ACTIVE_LO, _ACTIVE_HI)
        cap = h - n_active
        n_decoy = ctx.draw_int("n_decoy_rows", min(d_lo, cap),
                               max(min(d_hi, cap), min(d_lo, cap)))
    elif d_override:
        n_decoy = ctx.draw_int("n_decoy_rows", _DECOY_LO, _DECOY_HI)
        cap = h - n_decoy
        if cap < 1:
            raise ValueError(
                f"n_decoy_rows={n_decoy} leaves no room for an active row "
                f"on grid_h={h}")
        n_active = ctx.draw_int("n_active_rows", min(a_lo, cap),
                                max(min(a_hi, cap), min(a_lo, cap)))
    else:
        n_active = ctx.draw_int("n_active_rows", a_lo, a_hi)
        cap = h - n_active
        n_decoy = ctx.draw_int("n_decoy_rows", min(d_lo, cap),
                               max(min(d_hi, cap), min(d_lo, cap)))

    g = full_grid(h, w, 7)
    rows = rng.sample(range(h), n_active + n_decoy)
    active_rows, decoy_rows = rows[:n_active], rows[n_active:]
    # Bars may reach the canonical extreme (7 non-7 cells on a 10-wide row);
    # the GLOBAL budget below keeps background 7 strictly modal instead of a
    # blunt per-row cap (KRF-0003: stay on the empirical manifold).
    for r in active_rows:
        bar_len = min(_bar_length(bar_kind, w, rng), 7)
        idx = _draw_idx(idx_kind, bar_len, rng)
        c6 = rng.randint(idx, w - 1 - (bar_len - 1 - idx))
        left_cols = rng.sample(range(0, c6), idx) if idx > 0 else []
        right_cols = (rng.sample(range(c6 + 1, w), bar_len - 1 - idx)
                      if bar_len - 1 - idx > 0 else [])
        g[r][c6] = 6
        for c in list(left_cols) + list(right_cols):
            g[r][c] = rng.choice(palette)
    for r in decoy_rows:
        k = min(rng.randint(*decoy_cells), 6)
        for c in rng.sample(range(w), k):
            g[r][c] = rng.choice(palette)
    _enforce_modal_budget(g, active_rows, decoy_rows, rng)
    return g


def _enforce_modal_budget(g, active_rows, decoy_rows, rng):
    """Trim non-7 cells until 7 is strictly the most frequent color.

    Exact plurality check (not a majority proxy): canonical grids reach
    54 non-7 cells on 10x10 with 7 still modal, so bars up to the
    canonical 7-cell extreme survive.  The trim only binds on pathological
    small-canvas count overrides.  Decoy rows are trimmed first (down to
    one cell, so the exact row count is preserved); active rows then lose
    non-anchor cells (down to three, keeping the self_check bar minimum).
    Trimming a non-anchor cell only shrinks the row's non-7 count, which
    always keeps the bar in bounds."""

    def violates():
        freq = {}
        for row in g:
            for v in row:
                freq[v] = freq.get(v, 0) + 1
        top_other = max((n for c, n in freq.items() if c != 7), default=0)
        return freq.get(7, 0) <= top_other

    for r in decoy_rows:
        while violates() and sum(v != 7 for v in g[r]) > 1:
            cells = [c for c, v in enumerate(g[r]) if v != 7]
            g[r][rng.choice(cells)] = 7
    for r in active_rows:
        while violates() and sum(v != 7 for v in g[r]) > 3:
            cells = [c for c, v in enumerate(g[r]) if v not in (6, 7)]
            g[r][rng.choice(cells)] = 7
