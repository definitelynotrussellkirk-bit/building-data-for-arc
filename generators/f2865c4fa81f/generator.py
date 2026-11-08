"""Generator for 770cc55f.

Rule: a tall narrow grid carries one all-2 separator row, one contiguous
bar row above it and one contiguous bar row below it, both bars in the same
non-{2,4} color.  The intersection of the two bars' columns is filled with
color 4 between the WIDER bar and the separator (strictly more columns; the
narrower side is never filled).

Bars are contiguous runs (canonical-true).  Most draws keep the narrower
bar's columns inside the wider bar's, but a band-dependent share of draws
lets the narrower bar spill columns outside the wider bar — only the shared
columns fill, which is the disambiguating witness against the shortcut
"fill the narrower bar's columns".  The wider bar always keeps at least one
empty row toward the separator, so the rule's fill is never empty and the
output always differs from the input.

About 30% of default draws choose one complete official linked profile
(dimensions, width ordering, subset relation, edge rows, and normalized
top/bottom runs) before varying the bar color and any lawful common horizontal
translation. This retains the demonstrated morphology without replaying only
the five literal grids.

Combinatorial axes (6): grid_h, grid_w, top_wider, strict_subset,
palette_kind, texture.
Branches exercised: top-wider / bot-wider fills, subset / non-subset bars,
bar positions (rows 0 / h-1 included), bar widths 1..w, intersection sizes
1..w-1, palette pools.
Edge textures (all crash-free for the oracle): edge_bars,
narrow_touching_sep, full_width, single_shared_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f2865c4fa81f"
VERSION = "3.3.0"
TASK_ID = "f2865c4fa81f"
RULE_HASH = "2e1f5a047527"
SUMMARY = ("All-2 separator row; same-color contiguous bars above and below. "
           "Columns present in BOTH bars fill with 4 between the wider bar "
           "and the separator.")

# Rivals: 'fill the narrower bar's columns' refuted by non-subset demos where
# the narrower bar spills columns outside the wider bar (those stay 0).
# 'fill above and below the separator' refuted by every demo (only the wider
# side fills). 'output is input' refuted by every demo (the wider side
# always keeps >=1 fill row and the intersection is non-empty). 'use the bar
# color for the fill' refuted by every demo (fill is always 4). 'separator
# position encodes the side' refuted: sep is always h//2, the side comes from
# the width comparison.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one all-2 separator row at h//2; no other 2-cells anywhere",
    "top half: exactly one contiguous bar row; bot half: exactly one contiguous bar row",
    "both bars share one color, never 2 (separator) or 4 (fill); no 4-cells in the input",
    "bar widths are strictly unequal; the column intersection is non-empty",
    "the wider bar keeps at least one empty row toward the separator",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
EDGE_TEXTURES = ("edge_bars", "narrow_touching_sep", "full_width",
                 "single_shared_col")
HELPFUL_TEXTURES = EDGE_TEXTURES

AXES = {
    "grid_h":       {"type": "int", "default": "band rng 9..24", "valid": "9..24"},
    "grid_w":       {"type": "int", "default": "band rng 4..11", "valid": "4..11"},
    "top_wider":    {"type": "bool", "default": "rng", "valid": "true|false"},
    "strict_subset": {"type": "bool",
                      "default": "canonical prior or band rng "
                                 "(easy 90%, medium 75%, hard 60%)",
                      "valid": "true|false"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "|".join(PALETTE_KINDS)},
    "texture":      {"type": "str", "default": "none",
                     "valid": "none|" + "|".join(EDGE_TEXTURES)},
}

# Complete official morphology after quotienting only common horizontal
# translation and bar color, both of which the rule ignores.  Each archetype
# is (height, width, normalized top run, normalized bottom run); both bars are
# on the outer rows and the combined run starts at normalized column zero.
_CANONICAL_ARCHETYPES = (
    (13, 5, (1, 2), (0, 1, 2, 3)),
    (13, 5, (0, 1, 2, 3), (1, 2, 3)),
    (13, 6, (2, 3), (0, 1, 2, 3, 4)),
    (9, 4, (1, 2, 3), (0, 1)),
    (11, 5, (0, 1, 2, 3, 4), (1, 2)),
)


def _validate_call(difficulty, overrides):
    """Reject unsupported controls instead of silently coercing/falling back."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    for label in ("top_wider", "strict_subset"):
        value = overrides.get(label)
        if value is not None and type(value) is not bool:
            raise ValueError(f"{label} must be a bool")
    for label in ("palette_kind", "texture"):
        value = overrides.get(label)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{label} must be a string")


# --------------------------------------------------------------------------
# Structural validation (input side only — outputs always come from the
# canonical Racket rule).
# --------------------------------------------------------------------------

def _runs(cols):
    """Split a sorted column list into contiguous runs."""
    runs = []
    start = prev = None
    for i, c in enumerate(cols):
        if i and c != prev + 1:
            runs.append((start, prev))
            start = c
        elif not i:
            start = c
        prev = c
    if cols:
        runs.append((start, prev))
    return runs


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance (all five canonical pairs
    satisfy them): rectangular 0..9 grid; exactly one all-2 separator row at
    h//2 and no other 2-cells; all other non-zero cells share one color C
    not in {2,4} with no 4-cells present; exactly one contiguous bar row
    above and one below the separator; bar widths strictly unequal with a
    non-empty column intersection; the wider bar keeps at least one empty
    row toward the separator so the oracle's fill is never empty. Rejects
    every input on which the oracle crashes (missing separator or missing
    bar) and any extra/moved bar row."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if not 9 <= h <= 24:
        errs.append(f"height {h} outside declared 9..24 envelope")
    if not 4 <= w <= 11:
        errs.append(f"width {w} outside declared 4..11 envelope")
    if any(type(v) is not int or not 0 <= v <= 9
           for row in grid for v in row):
        errs.append("cells must be integer colors in 0..9")
        return errs
    sep_rows = [r for r in range(h) if all(v == 2 for v in grid[r])]
    if len(sep_rows) != 1:
        errs.append(f"expected exactly one all-2 separator row, got {len(sep_rows)}")
        return errs
    sep = sep_rows[0]
    if sep != h // 2:
        errs.append(f"separator row {sep} is not h//2 ({h // 2})")
    if any(grid[r][c] == 2 for r in range(h) for c in range(w) if r != sep):
        errs.append("2-cells outside the separator row")
    others = sorted({grid[r][c] for r in range(h) for c in range(w)
                     if grid[r][c] not in (0, 2)})
    if len(others) != 1:
        errs.append(f"bar cells must share exactly one color, got {others}")
        return errs
    color = others[0]
    if color == 4:
        errs.append("bar color must not be 4 (the fill color)")
    top_rows = [r for r in range(sep) if any(v == color for v in grid[r])]
    bot_rows = [r for r in range(sep + 1, h) if any(v == color for v in grid[r])]
    if len(top_rows) != 1:
        errs.append(f"expected exactly one top bar row, got {len(top_rows)}")
        return errs
    if len(bot_rows) != 1:
        errs.append(f"expected exactly one bot bar row, got {len(bot_rows)}")
        return errs
    top, bot = top_rows[0], bot_rows[0]
    top_cols = [c for c in range(w) if grid[top][c] == color]
    bot_cols = [c for c in range(w) if grid[bot][c] == color]
    if len(_runs(top_cols)) != 1:
        errs.append("top bar is not one contiguous run")
    if len(_runs(bot_cols)) != 1:
        errs.append("bot bar is not one contiguous run")
    if len(top_cols) == len(bot_cols):
        errs.append("bar widths must be strictly unequal (tie side is undefined)")
    inter = set(top_cols) & set(bot_cols)
    if not inter:
        errs.append("column intersection is empty (rule would not fire)")
    if len(top_cols) > len(bot_cols) and top >= sep - 1:
        errs.append("wider top bar is adjacent to the separator (empty fill)")
    if len(bot_cols) > len(top_cols) and bot <= sep + 1:
        errs.append("wider bot bar is adjacent to the separator (empty fill)")
    return errs


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

def _build_palette(kind):
    if kind == "warm":
        pool = [3, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 3]
    elif kind == "broad":
        pool = [1, 3, 5, 6, 7, 8, 9]
    else:
        raise ValueError(f"unknown palette_kind {kind!r}")
    return [c for c in pool if c not in (2, 4)]


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; overrides validated against the full valid
    range (an override must execute on any band, per the AXES contract)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def observe_overrides(grid):
    """Report per-draw realized values of exact semantic axes (KRF-0002),
    derived from the grid itself: top_wider compares the two bar rows' run
    lengths; strict_subset is True when the shorter run is a subset of the
    longer one. The separator row (color 2) is excluded."""
    h, w = len(grid), len(grid[0])
    runs = []
    for r in range(h):
        cols = [c for c in range(w) if grid[r][c] not in (0, 2)]
        if cols:
            runs.append((r, cols))
    if len(runs) != 2:
        return {"top_wider": None, "strict_subset": None}
    (rt, ct), (rb, cb) = runs
    top_wider = len(ct) > len(cb)
    longer, shorter = (ct, cb) if top_wider else (cb, ct)
    strict = set(shorter) <= set(longer)
    return {"top_wider": top_wider, "strict_subset": strict}


def _normalized_run_pair(top_cols, bot_cols):
    """Normalize only the common horizontal translation."""
    origin = min((*top_cols, *bot_cols))
    top_norm = tuple(c - origin for c in top_cols)
    bot_norm = tuple(c - origin for c in bot_cols)
    return top_norm, bot_norm


def canonical_profile_signature(grid):
    """Return the complete linked bar signature, normalized for translation.

    The signature intentionally retains every answer-bearing feature used by
    the rule: canvas dimensions, side ordering, subset relation, bar widths,
    overlap width, vertical gaps from the outer edges, and the relative
    top/bottom runs. Only bar color and common horizontal translation are
    quotiented out.
    """
    if self_check(grid):
        return None
    h, w = len(grid), len(grid[0])
    sep = h // 2
    bar_color = next(
        value
        for row in grid
        for value in row
        if value not in (0, 2)
    )
    top_row = next(
        r for r in range(sep) if bar_color in grid[r]
    )
    bot_row = next(
        r for r in range(sep + 1, h) if bar_color in grid[r]
    )
    top_cols = tuple(
        c for c in range(w) if grid[top_row][c] == bar_color
    )
    bot_cols = tuple(
        c for c in range(w) if grid[bot_row][c] == bar_color
    )
    top_norm, bot_norm = _normalized_run_pair(top_cols, bot_cols)
    top_wider = len(top_cols) > len(bot_cols)
    longer, shorter = (
        (top_cols, bot_cols) if top_wider else (bot_cols, top_cols)
    )
    strict_subset = set(shorter) <= set(longer)
    return (
        h,
        w,
        top_wider,
        strict_subset,
        len(top_cols),
        len(bot_cols),
        len(set(top_cols) & set(bot_cols)),
        top_row,
        h - 1 - bot_row,
        top_norm,
        bot_norm,
    )


def _archetype_signature(archetype):
    h, w, top_run, bot_run = archetype
    top_norm, bot_norm = _normalized_run_pair(top_run, bot_run)
    top_wider = len(top_run) > len(bot_run)
    longer, shorter = (
        (top_run, bot_run) if top_wider else (bot_run, top_run)
    )
    return (
        h,
        w,
        top_wider,
        set(shorter) <= set(longer),
        len(top_run),
        len(bot_run),
        len(set(top_run) & set(bot_run)),
        0,
        0,
        top_norm,
        bot_norm,
    )


_CANONICAL_SIGNATURES = frozenset(
    _archetype_signature(archetype)
    for archetype in _CANONICAL_ARCHETYPES
)


def is_canonical_profile(grid):
    """Whether ``grid`` matches one complete official linked morphology."""
    return canonical_profile_signature(grid) in _CANONICAL_SIGNATURES


def rule_mirror(grid):
    """Small independent Python statement of the canonical Racket rule."""
    h, w = len(grid), len(grid[0])
    sep = next(r for r in range(h) if all(value == 2 for value in grid[r]))
    top_row = next(
        r for r in range(sep)
        if any(value not in (0, 2) for value in grid[r])
    )
    bot_row = next(
        r for r in range(sep + 1, h)
        if any(value not in (0, 2) for value in grid[r])
    )
    top_cols = [
        c for c in range(w) if grid[top_row][c] != 0
    ]
    bot_cols = [
        c for c in range(w) if grid[bot_row][c] != 0
    ]
    shared = set(top_cols) & set(bot_cols)
    if len(top_cols) > len(bot_cols):
        fill_rows = range(top_row + 1, sep)
    else:
        fill_rows = range(sep + 1, bot_row)
    result = [row[:] for row in grid]
    for r in fill_rows:
        for c in shared:
            result[r][c] = 4
    return result


def _pick_bars(rng, w, n_more, n_less, strict_subset):
    """Contiguous column runs for the wider and narrower bars. In non-subset
    mode (geometry permitting) the narrower run overlaps the wider run in
    >=1 column and spills >=1 column past one of its edges."""
    more_start = rng.randint(0, w - n_more)
    wider = list(range(more_start, more_start + n_more))
    candidates = []
    if not strict_subset and n_more < w:
        for s in range(0, w - n_less + 1):
            run = list(range(s, s + n_less))
            overlap = len(set(run) & set(wider))
            if 0 < overlap < n_less:
                candidates.append(run)
    if candidates:
        narrower = rng.choice(candidates)
    elif strict_subset:
        start = rng.randint(more_start, more_start + n_more - n_less)
        narrower = list(range(start, start + n_less))
    else:
        raise ValueError(
            "non-subset bar geometry has no overlapping spill placement"
        )
    return wider, narrower


def _single_shared_bars(rng, w, strict_subset):
    """Bar runs whose column intersection is exactly one column. Subset mode
    uses a 1-cell narrower bar inside the wider run; non-subset mode uses a
    narrower run overlapping the wider run in exactly one column and
    spilling past one edge."""
    if strict_subset:
        n_more = rng.randint(2, w)
        more_start = rng.randint(0, w - n_more)
        wider = list(range(more_start, more_start + n_more))
        s = rng.randint(more_start, more_start + n_more - 1)
        return wider, [s]
    candidates = []
    for n_more in range(3, w):
        for n_less in range(2, n_more):
            for more_start in range(0, w - n_more + 1):
                wider = list(range(more_start, more_start + n_more))
                for less_start in range(0, w - n_less + 1):
                    narrower = list(
                        range(less_start, less_start + n_less)
                    )
                    if len(set(narrower) & set(wider)) == 1:
                        candidates.append((wider, narrower))
    if not candidates:
        raise ValueError(
            "single_shared_col has no non-subset placement"
        )
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, w_lo, w_hi = 9, 13, 4, 6
        subset_options = [True] * 9 + [False]
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi = 17, 24, 7, 11
        subset_options = [True, True, True, False, False]
    else:
        h_lo, h_hi, w_lo, w_hi = 11, 16, 5, 8
        subset_options = [True, True, True, False]

    # Fixed "none" is the default texture. An explicit "none" follows the
    # identical path; named modes are validated and recorded through GenCtx.
    if overrides.get("texture") is not None:
        texture_name = ctx.draw_choice(
            "texture", ["none", *EDGE_TEXTURES]
        )
    else:
        texture_name = ctx.draw_choice("texture", ["none"])
    texture = None if texture_name == "none" else texture_name
    palette_kind = ctx.draw_choice(
        "palette_kind", list(PALETTE_KINDS)
    )
    color = ctx.draw_choice(
        f"bar_color|{band}", _build_palette(palette_kind)
    )

    # Default-only complete-profile prior. Explicit exact geometry controls
    # bypass it; explicit palette_kind remains compatible and is honored.
    canon = None
    exact_override = any(
        overrides.get(label) is not None
        for label in ("grid_h", "grid_w", "top_wider", "strict_subset")
    )
    if texture is None and not exact_override:
        if ctx.draw_rng(f"canonical_prior|{band}").random() < 0.30:
            canon = ctx.draw_choice(
                f"canonical_form|{band}",
                list(_CANONICAL_ARCHETYPES),
            )

    geometry_rng = ctx.draw_rng("bar_geometry")
    if canon is not None:
        h, w, top_template, bot_template = canon
        span = max((*top_template, *bot_template)) + 1
        h = ctx.draw_int("grid_h", h, h)
        w = ctx.draw_int("grid_w", w, w)
        top_wider = ctx.draw_choice(
            "top_wider", [len(top_template) > len(bot_template)]
        )
        longer, shorter = (
            (top_template, bot_template)
            if top_wider else (bot_template, top_template)
        )
        strict_subset = ctx.draw_choice(
            "strict_subset", [set(shorter) <= set(longer)]
        )
        shift = ctx.draw_rng(
            f"canonical_translation|{band}"
        ).randint(0, w - span)
        top_cols = [c + shift for c in top_template]
        bot_cols = [c + shift for c in bot_template]
    else:
        h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, 9, 24)
        w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, 4, 11)
        top_wider = ctx.draw_choice("top_wider", [True, False])
        # A full-width wider bar cannot support a non-subset spill. Constrain
        # the default draw to its feasible singleton; an explicit False is
        # rejected by draw_choice instead of being silently replaced.
        if texture == "full_width":
            strict_options = [True]
        elif overrides.get("strict_subset") is not None:
            # Explicit globally valid controls are band-independent.
            strict_options = [True, False]
        else:
            strict_options = subset_options
        strict_subset = ctx.draw_choice("strict_subset", strict_options)

        if texture == "full_width":
            wider, narrower = _pick_bars(
                geometry_rng,
                w,
                w,
                geometry_rng.randint(1, w - 1),
                True,
            )
        elif texture == "single_shared_col":
            wider, narrower = _single_shared_bars(
                geometry_rng, w, strict_subset
            )
        else:
            # Non-subset mode must realize a genuine spill: the wider bar
            # leaves an outside column and the narrower bar has width >=2.
            if strict_subset:
                n_more = geometry_rng.randint(2, w)
                n_less = geometry_rng.randint(1, n_more - 1)
            else:
                n_more = geometry_rng.randint(3, w - 1)
                n_less = geometry_rng.randint(2, n_more - 1)
            wider, narrower = _pick_bars(
                geometry_rng, w, n_more, n_less, strict_subset
            )
        top_cols, bot_cols = (wider, narrower) if top_wider else (narrower, wider)

    sep = h // 2
    row_rng = ctx.draw_rng("bar_rows")
    if canon is not None:
        top_row, bot_row = 0, h - 1
    elif texture == "edge_bars":
        top_row, bot_row = 0, h - 1
    elif texture == "narrow_touching_sep":
        if top_wider:
            top_row = row_rng.randint(0, sep - 2)
            bot_row = sep + 1
        else:
            top_row = sep - 1
            bot_row = row_rng.randint(sep + 2, h - 1)
    else:
        top_row = row_rng.randint(0, sep - 2)
        bot_row = row_rng.randint(sep + 2, h - 1)

    g = full_grid(h, w, 0)
    for c in range(w):
        g[sep][c] = 2
    for c in top_cols:
        g[top_row][c] = color
    for c in bot_cols:
        g[bot_row][c] = color
    return g
