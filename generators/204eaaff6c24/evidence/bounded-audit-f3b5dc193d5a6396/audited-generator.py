"""Generator for puzzle d631b094.

Rule: find the first non-zero color present (the input carries exactly
one), count its cells n, and emit a 1 x n bar of that color
(`encode-bar n n color` — the corpus-rare prelude primitive this task
exercises).

Canonical pairs are always 3x3 with 1..5 cells of one color.  The
generator carries an explicit canonical prior (KRF-0003): 30% of default
draws on every band land exactly on that family (3x3, one color, 1..5
cells), while generalized draws extend canvas (up to 12x12), count (up to
30, the ARC output-bar limit), and layout (rows, columns, diagonals,
clusters, blobs, scattered, random).

Combinatorial axes (6): grid_h/w, fg_color, n_cells, fg_layout, texture
(alias for fg_layout).  The old degenerate textures (single_cell /
all_filled / monochrome_no_bg) were removed: exact counts via n_cells
cover them honestly, and an all-filled grid violates the canonical
at-least-one-background-cell shape the self_check enforces.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "204eaaff6c24"
VERSION = "2.0.0"  # distribution break over 1.1.0: declared envelope
# narrowed to the tapped 3..12 range, exact n_cells/fg_color with
# observe_overrides, canonical prior 0.30 (3x3 + count 1..5), structural
# self_check, pinned RULE_HASH, degenerate textures removed.
TASK_ID = "204eaaff6c24"
RULE_HASH = "4571597a8055"
SUMMARY = (
    "0-bg grid with cells of EXACTLY ONE non-zero color (count 1..30, at "
    "least one 0 left). Rule: output a 1 x N bar of that color, where N "
    "is the cell count (encode-bar)."
)

INVARIANTS = [
    "background is 0 and at least one 0 cell remains",
    "exactly one non-zero color appears (any of 1..9)",
    "1..30 non-zero cells, so the 1 x N output bar fits ARC limits",
    "grid dims stay within 3..12 x 3..12",
]

FG_LAYOUTS = ("random", "cluster", "row", "column", "diagonal", "blob",
              "scattered")
DEGENERATE_TEXTURES: tuple = ()
HELPFUL_TEXTURES = FG_LAYOUTS

# Canonical prior (KRF-0003): default draws (no shape override) land on the
# exact canonical family (3x3, one color, 1..5 cells) with this probability
# on every band.  The canonical family holds 9 * sum(C(9,n), n=1..5) = 3429
# distinct inputs, so the prior does not measurably cap input diversity.
_CANONICAL_PRIOR_P = 0.30

_DIM_LO, _DIM_HI = 3, 12
_N_LO, _N_HI = 1, 30

AXES = {
    "grid_h":    {"type": "int", "default": "band rng 3..5 easy, 3..6 "
                      "medium, 6..12 hard; 30% of default draws pin the "
                      "canonical 3x3", "valid": "3..12"},
    "grid_w":    {"type": "int", "default": "band rng 3..5 easy, 3..6 "
                      "medium, 6..12 hard; 30% of default draws pin the "
                      "canonical 3x3", "valid": "3..12"},
    "fg_color":  {"type": "color", "default": "rng 1..9", "valid": "1..9"},
    "n_cells":   {"type": "int", "default": "band rng 1..8 easy, 1..15 "
                      "medium, 5..30 hard (1..5 on canonical-prior draws); "
                      "free dims grow to fit", "valid": "1..30"},
    "fg_layout": {"type": "str", "default": "rng helpful",
                  "valid": "|".join(FG_LAYOUTS)},
    "texture":   {"type": "str", "default": "alias for fg_layout",
                  "valid": "|".join(FG_LAYOUTS)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared envelope, colors 0..9, at least one background 0 left,
    exactly one non-zero color, and 1..30 non-zero cells (the output bar
    must fit ARC).  Band ranges are defaults only; difficulty is unused."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for row in grid for v in row):
        errs.append("color outside 0..9")
    if not (_DIM_LO <= h <= _DIM_HI and _DIM_LO <= w <= _DIM_HI):
        errs.append(f"dims {h}x{w} outside valid "
                    f"{_DIM_LO}..{_DIM_HI} x {_DIM_LO}..{_DIM_HI}")
    colors = {v for row in grid for v in row if v != 0}
    if not colors:
        errs.append("no non-zero cell (the rule has no color to count)")
    elif len(colors) > 1:
        errs.append(f"{len(colors)} non-zero colors {sorted(colors)}; "
                    f"exactly one allowed")
    n = sum(1 for row in grid for v in row if v != 0)
    if n > _N_HI:
        errs.append(f"{n} non-zero cells; output bar would exceed "
                    f"{_N_HI} cells")
    if n == h * w:
        errs.append("no background 0 cell left (canonical inputs always "
                    "keep background)")
    return errs


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0002),
    derived from the returned grid: the single non-zero color and its
    cell count."""
    colors = {v for row in grid or [] for v in row if v != 0}
    fg = next(iter(colors)) if len(colors) == 1 else None
    n = sum(1 for row in grid or [] for v in row if v != 0)
    return {"fg_color": fg, "n_cells": n}


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an explicit override is validated against
    the full declared valid range (overrides are band-independent,
    KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _layout_cells(layout, h, w, n, rng):
    if layout == "cluster":
        cr, cc = rng.randint(0, h - 1), rng.randint(0, w - 1)
        cells = [(r, c) for r in range(h) for c in range(w)]
        cells.sort(key=lambda rc: abs(rc[0] - cr) + abs(rc[1] - cc))
        return cells[:n]
    if layout == "row":
        r = rng.randint(0, h - 1)
        cells = [(r, c) for c in range(w)]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "column":
        c = rng.randint(0, w - 1)
        cells = [(r, c) for r in range(h)]
        rng.shuffle(cells)
        return cells[:n]
    if layout == "diagonal":
        return [(k, k) for k in range(min(h, w))][:n]
    if layout == "blob":
        cr, cc = rng.randint(0, h - 1), rng.randint(0, w - 1)
        cells = [(r, c) for r in range(h) for c in range(w)]
        cells.sort(key=lambda rc: max(abs(rc[0] - cr), abs(rc[1] - cc)))
        return cells[:n]
    if layout == "scattered":
        primary = [(r, c) for r in range(0, h, 2) for c in range(0, w, 2)]
        primary_set = set(primary)
        rest = [(r, c) for r in range(h) for c in range(w)
                if (r, c) not in primary_set]
        rng.shuffle(primary)
        rng.shuffle(rest)
        return (primary + rest)[:n]
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    return cells[:n]


def _layout_cap(layout, h, w):
    """Max cells a layout can host on an h x w canvas."""
    if layout == "row":
        return w
    if layout == "column":
        return h
    if layout == "diagonal":
        return min(h, w)
    return h * w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    band = difficulty or "medium"
    if band == "easy":
        d_lo, d_hi, n_lo, n_hi = 3, 5, 1, 8
    elif band == "hard":
        d_lo, d_hi, n_lo, n_hi = 6, 12, 5, 30
    else:
        d_lo, d_hi, n_lo, n_hi = 3, 6, 1, 15

    texture = overrides.get("texture")
    if texture is not None and texture not in FG_LAYOUTS:
        raise ValueError(
            f"unknown texture {texture!r}; valid: {FG_LAYOUTS}")
    if texture is not None and overrides.get("fg_layout") is not None:
        raise ValueError("texture and fg_layout are conflicting aliases; "
                         "pass only one")
    explicit_layout = texture or overrides.get("fg_layout")
    if explicit_layout is not None and explicit_layout not in FG_LAYOUTS:
        raise ValueError(f"unknown fg_layout {explicit_layout!r}")

    # Canonical prior (KRF-0003): only for default draws with no shape
    # override; every override bypasses it and stays exact.
    shape_override = any(
        overrides.get(k) is not None
        for k in ("grid_h", "grid_w", "fg_color", "n_cells",
                  "fg_layout", "texture"))
    canonical_draw = not shape_override and rng.random() < _CANONICAL_PRIOR_P
    if canonical_draw:
        d_lo = d_hi = 3
        n_lo, n_hi = 1, 5

    n_override = overrides.get("n_cells")
    n = None
    h_lo, h_hi = d_lo, d_hi
    w_lo, w_hi = d_lo, d_hi
    if n_override is not None:
        n = int(n_override)
        # Free dims may grow (within the valid envelope) to host the
        # requested count plus one background cell; explicitly overridden
        # dims are exact and may not be exceeded.  need <= 31 always fits
        # (3 x 11 = 33), so only contradictory exact combos reject.
        need = n + 1
        if overrides.get("grid_h") is not None and \
                overrides.get("grid_w") is not None:
            if overrides["grid_h"] * overrides["grid_w"] < need:
                raise ValueError(
                    f"n_cells={n} + background cannot fit the exact "
                    f"{overrides['grid_h']}x{overrides['grid_w']} canvas")
        elif overrides.get("grid_w") is not None:
            h_need = -(-need // overrides["grid_w"])
            if h_need > _DIM_HI:
                raise ValueError(
                    f"n_cells={n} + background cannot fit grid_w="
                    f"{overrides['grid_w']} within the declared envelope")
            h_lo = max(h_lo, h_need)
            h_hi = max(h_hi, h_lo)

    h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, _DIM_LO, _DIM_HI)
    if n is not None and overrides.get("grid_w") is None:
        need = n + 1
        w_need = -(-need // h)
        if w_need > _DIM_HI:
            raise ValueError(
                f"n_cells={n} + background cannot fit grid_h={h} within "
                f"the declared envelope")
        w_lo = max(w_lo, w_need)
        w_hi = max(w_hi, w_lo)
    w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, _DIM_LO, _DIM_HI)
    if n is not None and h * w < n + 1:
        raise ValueError(
            f"n_cells={n} + background cannot fit the exact {h}x{w} canvas")
    fg = ctx.draw_color("fg_color", exclude={0})

    if explicit_layout is not None:
        layout = explicit_layout
        cap = _layout_cap(layout, h, w)
        if n is not None and n > cap:
            raise ValueError(
                f"n_cells={n} cannot fit layout {layout!r} on {h}x{w} "
                f"(cap {cap})")
    else:
        pool = [l for l in FG_LAYOUTS
                if n is None or _layout_cap(l, h, w) >= n]
        if not pool:
            raise ValueError(
                f"n_cells={n} fits no layout on {h}x{w}")
        layout = ctx.draw_choice("fg_layout", pool)

    if n is None:
        cap = min(n_hi, _layout_cap(layout, h, w), h * w - 1)
        lo = min(n_lo, cap)
        n = ctx.draw_int("n_cells", lo, max(lo, cap))
    else:
        n = ctx.draw_int("n_cells", _N_LO, min(_N_HI, h * w - 1))

    g = full_grid(h, w, 0)
    for (r, c) in _layout_cells(layout, h, w, n, rng):
        g[r][c] = fg
    return g
