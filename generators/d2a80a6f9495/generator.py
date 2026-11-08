"""Generator for 45737921 (swap 2 colors within each multicolor object).

Rule: for each 8-connected non-bg object with exactly 2 distinct colors,
swap those two colors within the object. Objects with 1 or 3+ colors
stay unchanged.

The v1.x distribution emitted 1-3 small two-part blobs (~2 objects per
the linter's component count) while the canonical inputs hold 1-4
FULLY-FILLED 3x3 two-color objects with interlocking patterns
(checkerboards, stripes, center/column markers) — a per-color component
count around 7. v2.0.0 rebuilds on the canonical structure: fully-filled
3x3 two-color objects plus explicit NEGATIVE witnesses (1-color and
3-color objects) so the rule's exactly-2-colors selection branch is
learnable — canonical never exercises it. A 25% linked prior (KRF-0003)
pins one of the four official dimension/object-count tuples; a separate
30% family prior boosts no-negative scenes while leaving layouts and
patterns generalized. Adds a structural self_check (declared degenerate
modes accepted as edge-but-valid), an observe_overrides hook, and pins
RULE_HASH to the canonical rule.

Combinatorial axes: grid_h, grid_w, n_swap, n_neg, object patterns,
color pairs, positions, texture family.
Degenerates: single_color_blob, no_blobs, all_one_blob (all rule-valid).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d2a80a6f9495"
RULE_HASH = "c5c861d875d9"  # canonical rule this generator was written against
VERSION = "2.2.0"
TASK_ID = "d2a80a6f9495"
SUMMARY = (
    "0-background grid (h in [6, 14], w in [6, 16]) holding 1-4 "
    "FULLY-FILLED 3x3 OBJECTS that each use EXACTLY TWO colors in an "
    "interlocking pattern (checkerboard, row/column stripes, center or "
    "column markers, random mixes), plus 0-2 NEGATIVE objects (solid "
    "1-color blocks or 3-color blocks). Objects stay 8-separated. Rule "
    "(SWAP THE TWO COLORS OF EVERY 2-COLOR OBJECT): within every "
    "8-connected non-bg object that uses exactly two distinct colors, "
    "swap those two colors; objects with 1 or 3+ colors stay unchanged. "
    "Net: the two-color blocks invert their pattern; solid and "
    "3+ color blocks are untouched."
)

INVARIANTS = [
    "background is the unique modal color 0",
    "1-4 fully-filled 3x3 two-color objects (swap targets), 8-separated from each other",
    "0-2 negative objects (1-color or 3-color) that the rule must leave unchanged",
    "at least one 2-color object per normal draw (the rule always fires)",
    "declared degenerate modes (single_color_blob, no_blobs, all_one_blob) are edge-but-valid: the rule still runs",
]

HELPFUL_TEXTURES = ("checker", "stripes", "markers")
DEGENERATE_TEXTURES = ("single_color_blob", "no_blobs", "all_one_blob")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 6..14 (easy low, hard high)", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 6..16", "valid": "6..16"},
    "n_swap": {"type": "int", "default": "1-2 easy / 1-3 med / 2-4 hard", "valid": "1..4"},
    "n_neg":  {"type": "int", "default": "0-1 easy / 0-1 med / 1-2 hard", "valid": "0..2"},
    "texture": {"type": "str", "default": "none",
                "valid": "|".join(
                    ("none",) + HELPFUL_TEXTURES + DEGENERATE_TEXTURES
                )},
}

# Besides the exact linked-profile prior below, boost the canonical family's
# no-negative branch while leaving dimensions, layouts, colors, and patterns
# generalized.
_NO_NEGATIVE_PRIOR_PROB = 0.30

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_KING = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


# ---------------------------------------------------------------------------
# Object model (mirrors prelude objects-multicolor: 8-connected non-bg comps)
# ---------------------------------------------------------------------------

def _objects_multicolor(g):
    h, w = len(g), len(g[0])
    seen = set()
    objs = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in _KING:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            objs.append(comp)
    return objs


def _obj_colors(g, obj):
    return {g[r][c] for r, c in obj}


def rule_mirror(grid):
    """Python parity oracle; training outputs still come only from Racket."""
    out = [row[:] for row in grid]
    for obj in _objects_multicolor(grid):
        colors = sorted(_obj_colors(grid, obj))
        if len(colors) != 2:
            continue
        first, second = colors
        for row, col in obj:
            out[row][col] = (
                second if grid[row][col] == first else first
            )
    return out


# ---------------------------------------------------------------------------
# 3x3 two-color patterns (all fully filled, exactly 2 colors)
# ---------------------------------------------------------------------------

def _pattern_cells(kind, rng):
    """Return (a_cells, b_cells) partitioning the 3x3 block; both non-empty."""
    allc = [(r, c) for r in range(3) for c in range(3)]
    if kind == "checker":
        flip = rng.random() < 0.5
        a = [(r, c) for r in range(3) for c in range(3) if (r + c) % 2 == (0 if flip else 1)]
    elif kind == "stripes":
        if rng.random() < 0.5:      # row stripes: one row a, rest b
            k = rng.randrange(3)
            a = [(k, c) for c in range(3)]
        else:                        # column stripes: one column a, rest b
            k = rng.randrange(3)
            a = [(r, k) for r in range(3)]
        if rng.random() < 0.5:       # sometimes a 2-line minority
            k2 = rng.randrange(3)
            extra = ([(k2, c) for c in range(3)] if a[0][0] == a[-1][0]
                     else [(r, k2) for r in range(3)])
            a = sorted(set(a) | set(extra))
    elif kind == "markers":
        style = rng.choice(("center", "mid_col", "mid_row", "corners"))
        if style == "center":
            a = [(1, 1)]
        elif style == "mid_col":
            a = [(r, 1) for r in range(3)]
        elif style == "mid_row":
            a = [(1, c) for c in range(3)]
        else:
            a = [(r, c) for r in (0, 2) for c in (0, 2)]
    else:  # mixed: random 3-6 minority cells
        k = rng.randint(3, 6)
        a = rng.sample(allc, k)
    a = set(a)
    b = [p for p in allc if p not in a]
    if not a or not b:
        a = {(0, 0)}
        b = [p for p in allc if p not in a]
    return sorted(a), b


_FAMILY_OF = {"checker": ("checker",), "stripes": ("stripes",), "markers": ("markers",),
              None: ("checker", "stripes", "markers", "mixed")}


def _paint_swap_object(g, r0, c0, kind, ca, cb, rng):
    a_cells, b_cells = _pattern_cells(kind, rng)
    for dr, dc in a_cells:
        g[r0 + dr][c0 + dc] = ca
    for dr, dc in b_cells:
        g[r0 + dr][c0 + dc] = cb


def _paint_neg_object(g, r0, c0, colors, rng):
    """Negative witness: solid 1-color or 3-color filled 3x3 block."""
    if len(colors) == 1:
        for dr in range(3):
            for dc in range(3):
                g[r0 + dr][c0 + dc] = colors[0]
    else:
        for dr in range(3):
            for dc in range(3):
                g[r0 + dr][c0 + dc] = colors[(dr + dc) % 3]


# ---------------------------------------------------------------------------
# Placement (8-separation between objects)
# ---------------------------------------------------------------------------

def _capacity(h, w):
    """Max objects (3x3) that pack with Chebyshev-2 separation, also bounded
    by the sub-50% density budget (0 must stay the unique modal color)."""
    packing = max(1, (h + 1) // 4) * max(1, (w + 1) // 4)
    density = max(1, ((h * w) // 2 - 1) // 9)
    return min(packing, density)


def _place_objects(g, painters, rng):
    """Paint each object's 3x3 at a random spot, Chebyshev >= 2 from placed
    cells. painters: list of f(g, r0, c0). Returns True iff all placed."""
    h, w = len(g), len(g[0])
    blocked = set()
    for paint in painters:
        ok = False
        for _ in range(80):
            r0 = rng.randint(0, h - 3)
            c0 = rng.randint(0, w - 3)
            cells = {(r0 + dr, c0 + dc) for dr in range(3) for dc in range(3)}
            if cells & blocked:
                continue
            paint(g, r0, c0)
            for (r, c) in cells:
                blocked.add((r, c))
                for dr, dc in _KING:
                    blocked.add((r + dr, c + dc))
            ok = True
            break
        if not ok:
            return False
    return True


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def _resolve_counts(ctx, h, w):
    """Draw/override n_swap and n_neg exactly from the FEASIBLE joint domain
    (capacity of the drawn canvas), so no later stage ever trims or replaces
    a recorded count. Only mutually infeasible override combinations raise."""
    cap = _capacity(h, w)
    n_swap = ctx.draw_int_diff("n_swap", 1, min(4, cap))
    n_neg = ctx.draw_int_diff("n_neg", 0, min(2, max(0, cap - n_swap)))
    return n_swap, n_neg


def _build(ctx, rng, tex, h, w, n_swap, n_neg):
    fg = list(ctx.draw_distinct_colors("fg_colors", n=min(8, 2 * (n_swap + n_neg)), exclude={0}))
    painters = []
    families = _FAMILY_OF.get(tex, _FAMILY_OF[None])
    ci = 0
    for _i in range(n_swap):
        kind = families[rng.randrange(len(families))]
        ca, cb = fg[ci % len(fg)], fg[(ci + 1) % len(fg)]
        ci += 2
        painters.append(lambda g, r0, c0, k=kind, a=ca, b=cb: _paint_swap_object(g, r0, c0, k, a, b, rng))
    for _j in range(n_neg):
        if rng.random() < 0.5:
            cols = [fg[ci % len(fg)]]; ci += 1
        else:
            cols = [fg[ci % len(fg)], fg[(ci + 1) % len(fg)], fg[(ci + 2) % len(fg)]]; ci += 3
        painters.append(lambda g, r0, c0, cs=cols: _paint_neg_object(g, r0, c0, cs, rng))
    g = full_grid(h, w, 0)
    if not _place_objects(g, painters, rng):
        return None
    return g


def _fits(h, w, n_swap, n_neg):
    return _capacity(h, w) >= n_swap + n_neg


def _draw_degenerate(tex, ctx, rng, h, w):
    fg = list(ctx.draw_distinct_colors("fg_colors", n=3, exclude={0}))
    g = full_grid(h, w, 0)
    if tex == "single_color_blob":
        # one solid 1-color block — no 2-color object, rule output is identity
        r0 = rng.randint(0, h - 3)
        c0 = rng.randint(0, w - 3)
        _paint_neg_object(g, r0, c0, [fg[0]], rng)
        return g
    if tex == "no_blobs":
        return g
    if tex == "all_one_blob":
        # whole grid is one 8-connected 2-color mass — everything swaps
        for r in range(h):
            for c in range(w):
                g[r][c] = fg[0] if (r + c) % 2 == 0 else fg[1]
        return g
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    raw_texture = overrides.get("texture")
    if raw_texture in (None, "none"):
        tex = None
    elif raw_texture in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        tex = raw_texture
    else:
        raise ValueError(
            f"unknown texture {raw_texture!r}; valid: "
            + "|".join(("none",) + HELPFUL_TEXTURES + DEGENERATE_TEXTURES)
        )
    rng = ctx.draw_rng("layout" if tex is None else f"layout:{tex}")
    # Feasible domain BEFORE the draws (pause-wave drift class): when counts
    # are pinned, the canvas is drawn from dims whose capacity fits them
    # (with elbow room) instead of being silently grown after the fact.
    counts_pinned = (overrides.get("n_swap") is not None
                     or overrides.get("n_neg") is not None)
    # Canonical-form prior (KRF-0003): ~25% of fully-unoverridden draws pin
    # one of the four official linked profiles (h, w, n_swap, n_neg=0)
    # through keyed draws; object layouts/colors stay random.
    if (tex is None and not counts_pinned
            and overrides.get("grid_h") is None and overrides.get("grid_w") is None):
        if ctx.draw_rng("canonical_prior").random() < 0.25:
            profile = ctx.draw_choice(
                "canonical_form", [(7, 7, 1, 0), (8, 9, 2, 0),
                                   (12, 12, 4, 0), (13, 10, 3, 0)])
            ch, cw, cswap, cneg = profile
            for label, value in (("grid_h", ch), ("grid_w", cw),
                                 ("n_swap", cswap), ("n_neg", cneg)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)
            counts_pinned = True
    if counts_pinned:
        need = ((overrides.get("n_swap") or 1) + (overrides.get("n_neg") or 0)) + 1
        h_lo = next((hh for hh in range(6, 15)
                     if _capacity(hh, 16) >= need), None)
        if h_lo is None:
            raise ValueError(
                f"pinned counts n_swap={overrides.get('n_swap')}, "
                f"n_neg={overrides.get('n_neg')} exceed the 14x16 envelope")
        h = ctx.draw_int_diff("grid_h", h_lo, 14)
        w_lo = next((ww for ww in range(6, 17)
                     if _capacity(h, ww) >= need), None)
        if w_lo is None:
            raise ValueError(
                f"pinned counts exceed the capacity of grid_h={h}")
        w = ctx.draw_int_diff("grid_w", w_lo, 16)
    else:
        # Full declared ranges; difficulty only skews the free draws, so
        # every single-axis boundary override is accepted exactly on every band.
        h = ctx.draw_int_diff("grid_h", 6, 14)
        w = ctx.draw_int_diff("grid_w", 6, 16)
    if tex in DEGENERATE_TEXTURES:
        honored = {"texture", "grid_h", "grid_w"}
        extra = sorted(k for k, v in overrides.items()
                       if v is not None and k not in honored)
        if extra:
            raise ValueError(f"texture={tex} does not honor overrides {extra}")
        return _draw_degenerate(tex, ctx, rng, h, w)

    # Canonical-family prior: boost the no-negative branch. The separate
    # canonical_form branch above is the strict linked-profile prior. Decide
    # this before the sole count resolution so provenance has no overwritten
    # intermediate n_neg draw.
    prior = (tex is None
             and rng.random() < _NO_NEGATIVE_PRIOR_PROB
             and overrides.get("n_neg") in (None, 0))
    if prior and overrides.get("n_neg") is None:
        ctx.overrides["n_neg"] = 0

    n_swap, n_neg = _resolve_counts(ctx, h, w)

    # Exactness: the counts and dims drawn above are FINAL. Placement
    # retries are nuisance-only (families/colors/positions re-roll each
    # attempt); infeasible override combinations fail loudly.
    for _attempt in range(40):
        g = _build(ctx, rng, tex, h, w, n_swap, n_neg)
        if g is not None:
            return g
    if not _fits(h, w, n_swap, n_neg):
        raise ValueError(
            f"cannot fit n_swap={n_swap}+n_neg={n_neg} objects on grid {h}x{w}")
    raise ValueError(
        f"{TASK_ID}: could not place n_swap={n_swap}+n_neg={n_neg} objects "
        f"on grid {h}x{w} after 40 attempts (infeasible combination)")


# ---------------------------------------------------------------------------
# Contract hooks
# ---------------------------------------------------------------------------

def observe_overrides(grid) -> dict:
    """Report the realized per-draw values of the exact semantic axes.

    n_swap = objects with exactly 2 distinct colors (swap targets);
    n_neg = objects with 1 or 3+ colors (left unchanged by the rule).
    Counts are derived from the returned grid via the same 8-connected
    multicolor object model the rule uses."""
    out: dict = {}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return out
    out["grid_h"] = len(grid)
    out["grid_w"] = len(grid[0])
    objs = _objects_multicolor(grid)
    n2 = sum(1 for o in objs if len(_obj_colors(grid, o)) == 2)
    out["n_swap"] = n2
    out["n_neg"] = len(objs) - n2
    return out


def profile_signature(grid):
    """Linked returned-grid profile used by the canonical-prior audit."""
    observed = observe_overrides(grid)
    return (
        observed.get("grid_h"),
        observed.get("grid_w"),
        observed.get("n_swap"),
        observed.get("n_neg"),
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants for the two-color-object swap task.

    Declared degenerate modes are lawful edge cases (the rule still runs):
    no_blobs (empty grid), single_color_blob (only non-2-color objects),
    all_one_blob (grid-filling 2-color mass, no background left). Normal
    draws must have a modal-0 background, 1-4 exactly-2-color objects and
    at most 2 negative (1/3+ color) objects, all 8-separated."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if not (6 <= h <= 14):
        errors.append(f"grid height {h} outside declared envelope 6..14")
    if not (6 <= w <= 16):
        errors.append(f"grid width {w} outside declared envelope 6..16")
    colors = sorted({v for row in grid for v in row})
    if any(not isinstance(v, int) or v < 0 or v > 9 for v in colors):
        errors.append(f"colors outside 0..9: {colors}")
    objs = _objects_multicolor(grid)
    if not objs:
        # no_blobs degenerate is exactly the all-zero grid; any non-zero
        # cell without an object is not a declared form.
        if any(v != 0 for row in grid for v in row):
            errors.append("no_blobs degenerate must be the all-zero grid")
        return errors
    if 0 not in colors:
        # all_one_blob degenerate: no zero AND exactly two colors; a full
        # one-color or three-plus-color fill is not a declared form.
        if len(colors) != 2:
            errors.append("all_one_blob degenerate must hold exactly two "
                          "colors (no zero present)")
        return errors
    if len(objs) == 1 and len(_obj_colors(grid, objs[0])) == 1:
        # single_color_blob degenerate: exactly one solid filled 3x3
        # one-color block; singletons, solid 2x2s, lines, and other small
        # one-color shapes are not a declared form.
        o = objs[0]
        rows = [r for r, _ in o]
        cols = [c for _, c in o]
        if not (len(o) == 9 and max(rows) - min(rows) == 2
                and max(cols) - min(cols) == 2):
            errors.append("single_color_blob degenerate must be one solid "
                          "filled 3x3 one-color block")
        return errors
    # --- normal mode -------------------------------------------------------
    counts = {v: sum(row.count(v) for row in grid) for v in colors}
    if counts.get(0, 0) <= max((v for k, v in counts.items() if k != 0), default=0):
        errors.append("background color 0 must be the unique modal color")
    n2 = sum(1 for o in objs if len(_obj_colors(grid, o)) == 2)
    n_neg = len(objs) - n2
    if not (1 <= n2 <= 4):
        errors.append(f"expected 1-4 two-color swap objects, got {n2}")
    if n_neg > 2:
        errors.append(f"expected at most 2 negative objects, got {n_neg}")
    for o in objs:
        rows = [r for r, _ in o]
        cols = [c for _, c in o]
        if not (len(o) == 9 and max(rows) - min(rows) == 2 and max(cols) - min(cols) == 2):
            errors.append("every object must be a fully-filled 3x3 block")
            break
    return errors
