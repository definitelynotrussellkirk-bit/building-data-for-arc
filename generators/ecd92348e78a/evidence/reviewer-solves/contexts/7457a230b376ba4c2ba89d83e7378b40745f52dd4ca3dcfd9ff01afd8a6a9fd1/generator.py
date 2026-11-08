"""Generator for puzzle b7999b51 (bar chart of per-color bbox heights).

Rule: for each non-bg color, take the bbox HEIGHT of its cells (max_row -
min_row + 1); sort colors by height DESC; output a (max_height) x N bar
chart whose column c is a vertical bar of height_c cells of color_c.

The v2.x distribution drew grid_w from an h-derived range ([8,22] while
AXES declared 6..20 — the axis-honesty defect), had no self_check and no
RULE_HASH, and avoided all cell overlap, while the canonical blocks
STACK: each color owns a contiguous row band and later rectangles carve
earlier ones from the edges, yet every color keeps at least one cell in
its band's top and bottom rows (so the measured height is exact) and
one contiguous run per row. v3.0.0 fixes the axis lie (declared ranges
drawn in full, band-skewed), reproduces the canonical stacked-block
style (with a separated-block variant for diversity), adds a structural
self_check (declared degenerate modes accepted as edge-but-valid), an
observe_overrides hook, and pins RULE_HASH.

Combinatorial axes: grid_h, grid_w, n_colors, height_min/max bounds,
max_rect_width, palette_kind, position_bias, texture.
Degenerates: tied_heights, single_color, full_grid (all rule-valid).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ecd92348e78a"
RULE_HASH = "f25306709cb3"  # canonical rule this generator was written against
VERSION = "3.2.1"  # strict public-call/override contracts and executable semantic rivals; generation law unchanged
TASK_ID = "ecd92348e78a"
SUMMARY = (
    "0-bg grid (h in [6, 19], w in [6, 20]) with 2-5 non-bg colors. "
    "Each color owns a contiguous ROW BAND whose height is that color's "
    "bar height; within its band the color fills one contiguous run per "
    "row. Blocks may STACK: a later block's rectangle can carve an "
    "earlier block from an edge (never splitting a row into two runs), "
    "but every color keeps at least one cell in its band's top and "
    "bottom rows, so the bbox height of every color is exactly its band "
    "height. Band heights are DISTINCT across colors. Rule (BAR CHART "
    "OF BBOX HEIGHTS, SORTED DESC): for each non-bg color compute "
    "bbox-height = max_row - min_row + 1 over all its cells; sort "
    "colors by height DESC; output a (max_height) x N chart where "
    "column c is a vertical bar of height_c cells of color_c at the "
    "top, 0 below."
)

# Rivals: 'output is input' refuted by demos (output is a small bar
# chart). 'sort ascending' refuted by demos with tallest first.
# 'pick width instead of height' refuted by demos where widest !=
# tallest. 'recolor to one color' refuted by demos preserving colors.
# 3 demos with >=3 distinct-height colors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is the unique modal color 0 (normal draws)",
    "2-5 distinct non-bg colors; every color forms a contiguous row band with one contiguous run per row",
    "each color keeps >=1 cell in its band's top and bottom rows (bbox height == band height)",
    "band heights are DISTINCT across colors (the DESC sort is unambiguous)",
    "declared degenerate modes (tied_heights, single_color, full_grid) are edge-but-valid: the rule still runs",
]

POSITION_BIASES = ("scattered", "left_heavy", "right_heavy",
                   "evenly_spaced", "centered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("tied_heights", "single_color", "full_grid")
# These are intentionally edge-but-rule-valid families, not malformed draws.
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":       {"type": "int", "default": "difficulty-skewed 6..19 (easy low, hard high)", "valid": "6..19"},
    "grid_w":       {"type": "int", "default": "difficulty-skewed 6..20", "valid": "6..20"},
    "n_colors":     {"type": "int", "default": "2-3 easy / 3-4 med / 4-5 hard", "valid": "2..5"},
    "height_min":   {"type": "int", "default": "rng 1..4", "valid": "1..6"},
    "height_max":   {"type": "int", "default": "rng 6..10", "valid": "3..10"},
    "max_rect_width": {"type": "int", "default": "rng 1..5", "valid": "1..5"},
    "palette_kind": {"type": "str", "default": "rng helpful",
                     "valid": "|".join(PALETTE_KINDS)},
    "position_bias": {"type": "str", "default": "rng helpful",
                      "valid": "|".join(POSITION_BIASES)},
    "texture":      {"type": "str", "default": "alias for position_bias",
                     "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# Dynamic geometric conflicts carry ``incompatible_axes`` on the exception.
# The empty declaration opts into strict joint-override auditing without
# pretending that a finite table enumerates the capacity constraints.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_INT_AXIS_RANGES = {
    "grid_h": (6, 19),
    "grid_w": (6, 20),
    "n_colors": (2, 5),
    "height_min": (1, 6),
    "height_max": (3, 10),
    "max_rect_width": (1, 5),
}
_ENUM_AXIS_VALUES = {
    "palette_kind": PALETTE_KINDS,
    "position_bias": POSITION_BIASES,
    "texture": HELPFUL_TEXTURES + DEGENERATE_TEXTURES,
}
_DIFFICULTIES = (None, "easy", "medium", "hard")


class IncompatibleOverrides(ValueError):
    """A well-typed override combination cannot coexist in this domain."""

    def __init__(self, message, axes):
        self.incompatible_axes = tuple(sorted(set(axes)))
        suffix = ", ".join(self.incompatible_axes) or "unspecified"
        super().__init__(f"{message}; incompatible axes: {suffix}")


def _validate_call(seed, sample_index, difficulty, overrides):
    """Reject malformed public requests before randomness or coercion."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (bool is not accepted)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"difficulty must be one of {_DIFFICULTIES}")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_AXIS_RANGES:
            lo, hi = _INT_AXIS_RANGES[name]
            single_color_count = (
                name == "n_colors" and value == 1
                and overrides.get("texture") == "single_color"
            )
            if (type(value) is not int
                    or (not single_color_count and not lo <= value <= hi)):
                raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
        else:
            choices = _ENUM_AXIS_VALUES[name]
            if type(value) is not str or value not in choices:
                raise ValueError(f"{name} must be one of {choices}")


def _raise_override_conflict(message, overrides):
    axes = [name for name, value in overrides.items() if value is not None]
    raise IncompatibleOverrides(message, axes)

# Default draws use the canonical stacked-block construction with this
# probability (KRF-0003 canonical-manifold prior).
_CANONICAL_PRIOR_PROB = 0.30


# ---------------------------------------------------------------------------
# Per-color band structure (mirrors what the rule measures)
# ---------------------------------------------------------------------------

def _color_bands(g):
    """color -> (rmin, rmax, height) over all that color's cells."""
    bands = {}
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v != 0:
                lo_hi = bands.get(v)
                if lo_hi is None:
                    bands[v] = [r, r]
                else:
                    lo_hi[0] = min(lo_hi[0], r)
                    lo_hi[1] = max(lo_hi[1], r)
    return {c: (lo, hi, hi - lo + 1) for c, (lo, hi) in bands.items()}


def _is_contiguous_run(cols):
    return not cols or max(cols) - min(cols) == len(cols) - 1


def _color_structure_ok(g, color, rmin, rmax):
    """Every non-empty band row holds ONE contiguous run of `color`. Band
    rows fully covered by other colors are lawful (canonical stacks blocks);
    the band's top/bottom rows are non-empty by construction of the bbox."""
    for r in range(rmin, rmax + 1):
        cols = [c for c in range(len(g[0])) if g[r][c] == color]
        if cols and not _is_contiguous_run(cols):
            return False
    return True


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    while len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
    return pool[:n]


def _pick_columns(bias, w, n, rng):
    candidates = list(range(w))
    if bias == "left_heavy":
        return candidates[:n]
    if bias == "right_heavy":
        return candidates[-n:]
    if bias == "evenly_spaced":
        if n == 1:
            return [w // 2]
        # anchors span the full width (endpoints included) so the painted
        # columns provably cover >= half the grid width (branch predicate)
        return sorted({round(i * (w - 1) / (n - 1)) for i in range(n)})
    if bias == "centered":
        center = w // 2
        cs = [center - (n - 1) // 2 + i for i in range(n)]
        return [c for c in cs if 0 <= c < w][:n]
    rng.shuffle(candidates)
    return sorted(candidates[:n])


def _stacked_valid(rects):
    """Canonical block rule: painted in order, every earlier rect keeps >=1
    cell in its band's TOP and BOTTOM rows (so the measured bbox height is
    exactly the band height), and its surviving cells in every row form ONE
    contiguous run (later rects carve edges only, never split a row).
    Middle band rows may be fully covered by later blocks (canonical does
    this)."""
    for i, (r0, ht, c0, ww) in enumerate(rects):
        own = set(range(c0, c0 + ww))
        for row in range(r0, r0 + ht):
            covered = set()
            for (r2, ht2, c2, ww2) in rects[i + 1:]:
                if r2 <= row < r2 + ht2:
                    covered |= set(range(c2, c2 + ww2))
            surv = sorted(own - covered)
            if row in (r0, r0 + ht - 1) and not surv:
                return False
            if not _is_contiguous_run(surv):
                return False
    return True


# Observed official archetypes: (h, w, n_colors, frozenset of band heights).
# The canonical prior samples one of these tuples exactly and guarantees a
# carve (>=1 occluded color whose per-row widths vary).
_ARCHETYPES = (
    (10, 15, 3, (1, 2, 3)),
    (10, 15, 3, (1, 3, 4)),
    (19, 18, 4, (1, 3, 4, 5)),
    (12, 18, 5, (1, 2, 3, 5, 6)),
)


def _has_carve(g, palette):
    """At least one color whose per-row cell counts vary across its band —
    the stacked/occluded look of the canonical blocks."""
    bands = _color_bands(g)
    for color in palette:
        if color not in bands:
            continue
        lo, hi, _ht = bands[color]
        widths = {sum(1 for c in range(len(g[0])) if g[r][c] == color)
                  for r in range(lo, hi + 1)}
        if len(widths) > 1:
            return True
    return False


def _pick_archetype_simple(overrides, rng):
    """An exact official archetype tuple compatible with every CALLER-pinned
    override, or None. Eligibility reads the request only, never draws —
    the chosen tuple is then injected into ctx.overrides so the recorded
    draw equals the realized grid. Pinned height bounds skip the prior
    entirely: variants realize the pinned bound exactly, which keeps the
    bound behaviorally live."""
    if overrides.get("max_rect_width") is not None and overrides["max_rect_width"] < 2:
        return None  # a carve needs at least one block of width >= 2
    if overrides.get("position_bias") == "evenly_spaced":
        return None  # spread anchors can never overlap, so no carve is possible
    if overrides.get("height_min") is not None or overrides.get("height_max") is not None:
        return None  # pinned bounds are realized on the variant path instead
    cands = []
    for (ah, aw, an, ahs) in _ARCHETYPES:
        if overrides.get("grid_h") is not None and overrides["grid_h"] != ah:
            continue
        if overrides.get("grid_w") is not None and overrides["grid_w"] != aw:
            continue
        if overrides.get("n_colors") is not None and overrides["n_colors"] != an:
            continue
        cands.append((ah, aw, an, tuple(sorted(ahs))))
    if not cands:
        return None
    return cands[rng.randrange(len(cands))]


def _bias_region(bias, w):
    """Inclusive column region a named bias constrains ALL painted cells into
    (its branch predicate is then 100% by construction)."""
    if bias == "left_heavy":
        return (0, max(0, w // 2 - 1))
    if bias == "right_heavy":
        return (w // 2, w - 1)
    if bias == "centered":
        return (max(0, w // 3), max(0, (2 * w) // 3 - 1))
    return (0, w - 1)


def _biased_c0(bias, anchor, ww, w, rng):
    """Column for one rect honoring the named bias; width is already clamped
    to the region size by the caller, so the whole rect stays in-region."""
    if bias in ("left_heavy", "right_heavy", "centered"):
        lo, hi = _bias_region(bias, w)
        return rng.randint(lo, max(lo, hi + 1 - ww))
    if bias == "evenly_spaced" and anchor is not None:
        return max(0, min(w - ww, anchor - ww // 2 + rng.randint(-1, 1)))
    return rng.randint(0, w - ww)


def _paint_carve_pair_constructive(h, w, palette, dims, rng):
    """CONSTRUCTIVE carve guarantee (archetype prior): the tallest rect is
    painted first, the second rect is placed to edge-carve exactly one
    column of it in one shared row at its bottom edge — so the tallest
    color's per-row widths vary (2 -> 1), by construction. Remaining rects
    are placed without touching any painted cell. The pair always validates
    (partial edge overlap: survivors stay contiguous and >= 1 cell), so an
    occluded varying-row-width color exists on every call."""
    order = sorted(range(len(dims)), key=lambda i: -dims[i][0])
    ci, cj = order[0], order[1]
    ht_i = dims[ci][0]
    ht_j = dims[cj][0]
    ww = 2  # carve pair width (within every archetype's width cap)
    # row bands overlapping by exactly one row at the carved rect's bottom
    r_i = rng.randint(0, h - ht_i - ht_j + 1)
    r_j = r_i + ht_i - 1
    c_i = rng.randint(0, w - 2 * ww)
    c_j = c_i + 1  # exactly one shared column (rect j eats rect i's right edge)
    g = full_grid(h, w, 0)
    for r in range(r_i, r_i + ht_i):
        for c in range(c_i, c_i + ww):
            g[r][c] = palette[ci]
    for r in range(r_j, r_j + ht_j):
        for c in range(c_j, c_j + ww):
            g[r][c] = palette[cj]
    used = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
    for k in order[2:]:
        color = palette[k]
        ht, wwk = dims[k]
        ok = False
        for _try in range(200):
            r0 = rng.randint(0, h - ht)
            c0 = rng.randint(0, w - wwk)
            cells = [(r0 + dr, c0 + dc) for dr in range(ht) for dc in range(wwk)]
            if any(p in used for p in cells):
                continue
            for (r, c) in cells:
                g[r][c] = color
                used.add((r, c))
            ok = True
            break
        if not ok:
            for c0 in range(w):
                for r0 in range(0, h - ht + 1):
                    cells = [(r0 + dr, c0) for dr in range(ht)]
                    if not any(p in used for p in cells):
                        for (r, c) in cells:
                            g[r][c] = color
                            used.add((r, c))
                        ok = True
                        break
                if ok:
                    break
        if not ok:
            return None
    return g


def _paint_stacked(h, w, palette, dims, anchors, rng, bias, require_carve=False):
    """Assign each color a (r0, ht, c0, ww) rectangle, validate the canonical
    stacked-block invariants, then paint in order (later overwrites).
    With require_carve, retry until at least one color is occluded (per-row
    widths vary) — the strict archetype family demands it."""
    for _attempt in range(60):
        rects = []
        for i, (ht, ww) in enumerate(dims):
            r0 = rng.randint(0, h - ht)
            anchor = anchors[i] if i < len(anchors) else None
            if bias in ("left_heavy", "right_heavy", "centered"):
                lo, hi = _bias_region(bias, w)
                ww = min(ww, hi - lo + 1)
            c0 = _biased_c0(bias, anchor, ww, w, rng)
            rects.append((r0, ht, c0, ww))
        if not _stacked_valid(rects):
            continue
        g = full_grid(h, w, 0)
        for color, (r0, ht, c0, ww) in zip(palette, rects):
            for r in range(r0, r0 + ht):
                for c in range(c0, c0 + ww):
                    g[r][c] = color
        if require_carve and not _has_carve(g, palette):
            continue
        return g
    return None


def _paint_separated(h, w, palette, dims, anchors, rng, bias):
    """Variant: rectangles avoid cell overlap entirely (no stacking)."""
    g = full_grid(h, w, 0)
    used = set()
    for i, (color, (ht, ww)) in enumerate(zip(palette, dims)):
        anchor = anchors[i] if i < len(anchors) else None
        if bias in ("left_heavy", "right_heavy", "centered"):
            lo, hi = _bias_region(bias, w)
            ww = min(ww, hi - lo + 1)
        ok = False
        for attempt in range(180):
            r0 = rng.randint(0, h - ht)
            c0 = _biased_c0(bias, anchor, ww, w, rng)
            cells = [(r0 + dr, c0 + dc) for dr in range(ht) for dc in range(ww)]
            if any(p in used for p in cells):
                continue
            for (r, c) in cells:
                g[r][c] = color
                used.add((r, c))
            ok = True
            break
        if not ok:
            return None
    return g


def _ffd_pack(heights, s, h):
    """First-fit-decreasing assignment of bars into s columns of capacity h.
    Returns the per-column index bins, or None when the set cannot pack."""
    bins = [[] for _ in range(s)]
    loads = [0] * s
    for idx, ht in sorted(enumerate(heights), key=lambda kv: -kv[1]):
        j = min(range(s), key=lambda j: loads[j])
        if loads[j] + ht > h:
            return None
        loads[j] += ht
        bins[j].append(idx)
    return bins


def _paint_bars_fallback(h, w, palette, heights, rng, bias="scattered"):
    """Deterministic safety net: 1-wide vertical bars packed by first-fit-
    decreasing into the bias region's columns (full width otherwise), each
    column stacked from row 0. Always succeeds when the heights pack."""
    g = full_grid(h, w, 0)
    if bias in ("left_heavy", "right_heavy", "centered"):
        lo, hi = _bias_region(bias, w)
        cols = list(range(lo, hi + 1))
    else:
        lo, cols = 0, list(range(w))
    pack = _ffd_pack(heights, len(cols), h)
    if pack is None:
        return None
    if bias == "evenly_spaced":
        # reassign the packed bins to span-covering columns (branch predicate:
        # painted columns cover >= half the grid width for 2+ colors)
        used = [j for j in range(len(cols)) if pack[j]]
        if len(used) > 1:
            cols = sorted({round(i * (w - 1) / (len(used) - 1)) for i in range(len(used))})
        else:
            cols = [w // 2]
        pack = [pack[j] for j in used]
    for j, idxs in enumerate(pack):
        r = 0
        for idx in idxs:
            for rr in range(r, r + heights[idx]):
                g[rr][cols[j]] = palette[idx]
            r += heights[idx]
    return g


def _draw_degenerate(tex, h, w, n_colors, rng):
    g = full_grid(h, w, 0)
    if tex == "tied_heights":
        # several colors, all with the SAME bar height (stable-sort ties)
        ht = rng.randint(2, min(4, h))
        cols = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_colors)
        anchors = sorted(rng.sample(range(w), min(n_colors, w)))
        for color, c in zip(cols, anchors):
            for r in range(ht):
                g[r][c] = color
        return g
    if tex == "single_color":
        ht = rng.randint(2, min(5, h))
        for r in range(ht):
            g[r][1] = 3
        return g
    if tex == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 3 if (r + c) % 2 == 0 else 4
        return g
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    tex = overrides.get("texture")
    rng = ctx.draw_rng("layout" if tex is None else f"layout:{tex}")

    # ---- canonical prior FIRST (KRF-0003): sample one of the four OBSERVED
    # archetype tuples exactly (h, w, n_colors, height-set) and force the
    # stacked mode with a guaranteed carve. The chosen tuple is injected
    # into ctx.overrides BEFORE the typed draws, so the recorded draw equals
    # the realized grid (no post-draw drift). Skipped whenever a pinned
    # override disagrees (overrides stay exact-or-loud).
    arch = None
    if tex is None and rng.random() < _CANONICAL_PRIOR_PROB:
        arch = _pick_archetype_simple(overrides, rng)
    arch_heights = None
    if arch is not None:
        ah, aw, an, arch_heights = arch
        ctx.overrides.setdefault("grid_h", ah)
        ctx.overrides.setdefault("grid_w", aw)
        ctx.overrides.setdefault("n_colors", an)
        ctx.overrides.setdefault("height_min", min(arch_heights))
        ctx.overrides.setdefault("height_max", max(arch_heights))
        ctx.overrides.setdefault("max_rect_width", 2)
    # Full declared ranges; difficulty only skews the free draws, so every
    # single-axis boundary override is accepted exactly on every band.
    h = ctx.draw_int_diff("grid_h", 6, 19)
    w = ctx.draw_int_diff("grid_w", 6, 20)
    h_min = ctx.draw_int_diff("height_min", 1, 6)
    h_max = ctx.draw_int_diff("height_max", 3, 10)
    ww_max = ctx.draw_int_diff("max_rect_width", 1, 5)
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    if tex in POSITION_BIASES and overrides.get("position_bias") not in (None, tex):
        _raise_override_conflict(
            f"texture={tex} already fixes position_bias; conflicting "
            f"position_bias={overrides.get('position_bias')!r}", overrides)
    bias = tex if tex in POSITION_BIASES else (
        overrides.get("position_bias")
        or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    if arch is not None and overrides.get("position_bias") is None:
        # a carve needs column-overlap freedom; a freely drawn bias yields to
        # scattered placement for archetype draws (evenly_spaced can never
        # overlap, and region clamps would starve the carve search)
        bias = "scattered"
    n_colors_req = overrides.get("n_colors")
    if tex in DEGENERATE_TEXTURES:
        honored = {"texture", "grid_h", "grid_w", "n_colors"}
        extra = sorted(k for k, v in overrides.items()
                       if v is not None and k not in honored)
        if extra:
            _raise_override_conflict(
                f"texture={tex} does not honor overrides {extra}", overrides)
        if tex == "single_color" and n_colors_req not in (None, 1):
            _raise_override_conflict(
                "texture=single_color is one-color: n_colors>1 is meaningless",
                overrides)
        if tex == "full_grid" and n_colors_req not in (None, 2):
            _raise_override_conflict(
                "texture=full_grid is two-color checker: n_colors!=2 is meaningless",
                overrides)
        nc_d = n_colors_req if n_colors_req is not None else 2
        return _draw_degenerate(tex, h, w, nc_d, rng)

    # ---- exactness resolution: overrides honored exactly or rejected ------
    # (a) span must host the requested number of distinct heights;
    # (b) the tallest requested height must fit the grid;
    # (c) the density domain [2, nc_hi] is feasible by construction.
    # Free parameters adapt; only fully-pinned infeasible requests raise.
    target_n = n_colors_req if n_colors_req is not None else 5
    while True:
        span = h_max - h_min + 1
        if n_colors_req is not None and span < target_n:
            if overrides.get("height_min") is None and h_min > max(1, h_max - target_n + 1):
                h_min = max(1, h_max - target_n + 1)      # free lower bound adapts
                continue
            if overrides.get("height_max") is None and h_max < min(h, 10, h_min + target_n - 1):
                h_max = min(h, 10, h_min + target_n - 1)  # free upper bound adapts
                continue
        if span < 2:
            if overrides.get("height_min") is None and h_min > 1:
                h_min -= 1
                continue
            if overrides.get("height_max") is None and h_max < min(h, 10):
                h_max += 1
                continue
            if overrides.get("grid_h") is None and h < 19:
                h += 1                    # free grid grows so the span can open
                continue
            _raise_override_conflict(
                f"need >= 2 distinct heights in [{h_min}, {h_max}]", overrides)
        if h_max > h:
            if overrides.get("height_max") is None:
                h_max = h                  # free bound adapts down to the grid
                continue
            if overrides.get("grid_h") is None and h < 19:
                h = min(19, h_max)          # free grid adapts to the tallest bar
                continue
            _raise_override_conflict(
                f"height_max={h_max} needs grid_h >= {h_max}, got {h}",
                overrides)
        span = h_max - h_min + 1
        budget = (h * w) // 2 - 1
        if bias in ("left_heavy", "right_heavy", "centered"):
            _lo, _hi = _bias_region(bias, w)
            budget = min(budget, (_hi - _lo + 1) * h)
        nc_hi = 2
        for n in range(2, 6):
            smallest = list(range(h_min, h_min + n))
            if n <= span and sum(smallest) <= budget and (
                    bias not in ("left_heavy", "right_heavy", "centered")
                    or _ffd_pack(smallest, _hi - _lo + 1, h) is not None):
                nc_hi = n
        # n=2 is always feasible on the >=6x6 envelope (2*h_min+1 <= 13 <= 17)
        if n_colors_req is None or nc_hi >= target_n:
            break
        if overrides.get("grid_h") is None and h < 19:
            h += 1
            continue
        if overrides.get("grid_w") is None and w < 20:
            w += 1
            continue
        if overrides.get("height_min") is None and h_min > 1:
            h_min -= 1
            continue
        _raise_override_conflict(
            f"cannot fit n_colors={target_n} distinct heights in "
            f"[{h_min}, {h_max}] within the density budget on {h}x{w}",
            overrides)
    n_colors = ctx.draw_int_diff("n_colors", 2, max(2, nc_hi))

    budget = (h * w) // 2 - 1           # 0 must stay the unique modal color
    region_cols = None
    if bias in ("left_heavy", "right_heavy", "centered"):
        _lo, _hi = _bias_region(bias, w)
        region_cols = (_lo, _hi)
        budget = min(budget, (_hi - _lo + 1) * h)   # region must also hold the bars
    palette = _build_palette(palette_kind, n_colors, rng)
    anchors = _pick_columns(bias, w, n_colors, rng)
    stacked = arch is not None or rng.random() < 0.5
    if arch_heights is not None:
        # Archetype prior: the exact observed height set (already fits every
        # archetype's density budget by construction).
        heights = list(arch_heights)
    else:
        # Pinned height bounds are REALIZED (a bar at each pinned bound, so
        # height_min/height_max override values are never inert); free bounds
        # sample across the range. Infeasible requests grow free dims, then
        # reject loudly only when fully pinned.
        forced = []
        if overrides.get("height_min") is not None:
            forced.append(h_min)
        if overrides.get("height_max") is not None and h_max != h_min:
            forced.append(h_max)
        while True:
            heights = None
            pool = [x for x in range(h_min, h_max + 1) if x not in forced]
            need = n_colors - len(forced)
            if 0 <= need <= len(pool):
                for _attempt in range(25):
                    cand = forced[:] + rng.sample(pool, need)
                    rng.shuffle(cand)
                    if sum(cand) <= budget and (
                            region_cols is None
                            or _ffd_pack(cand, region_cols[1] - region_cols[0] + 1, h) is not None):
                        heights = cand
                        break
                if heights is None and not forced:
                    cand = list(range(h_min, h_min + n_colors))
                    if sum(cand) <= budget and (
                            region_cols is None
                            or _ffd_pack(cand, region_cols[1] - region_cols[0] + 1, h) is not None):
                        heights = cand
                if heights is None and forced:
                    cand = sorted(forced + pool[:max(0, need)])
                    if len(cand) == n_colors and sum(cand) <= budget and (
                            region_cols is None
                            or _ffd_pack(cand, region_cols[1] - region_cols[0] + 1, h) is not None):
                        heights = cand
            if heights is not None:
                break
            if overrides.get("grid_h") is None and h < 19:
                h += 1
            elif overrides.get("grid_w") is None and w < 20:
                w += 1
            else:
                _raise_override_conflict(
                    f"cannot fit n_colors={n_colors} heights in [{h_min}, {h_max}] "
                    f"within the region/budget on {h}x{w}", overrides)
            budget = (h * w) // 2 - 1
            if region_cols is not None:
                _lo, _hi = _bias_region(bias, w)
                region_cols = (_lo, _hi)
                budget = min(budget, (_hi - _lo + 1) * h)
    # Widths share one remaining-cell budget. Each cap reserves width-1 room
    # for every later bar (reserve = sum of later heights), so the invariant
    # remaining >= height_i + reserve holds and total painted <= budget.
    dims = []
    remaining = budget
    for i, ht in enumerate(heights):
        reserve = sum(heights[i + 1:])
        cap = min(ww_max, w, (remaining - reserve) // ht)
        lo = 2 if (arch is not None and cap >= 2) else 1
        ww = rng.randint(lo, cap)
        dims.append((ht, ww))
        remaining -= ht * ww
    g = None
    if stacked:
        for _round in range(3 if arch is not None else 1):
            g = _paint_stacked(h, w, palette, dims, anchors, rng, bias,
                               require_carve=arch is not None)
            if g is not None:
                break
    if g is None and arch is not None:
        # constructive guarantee (not rejection sampling): lock a 1-column
        # edge carve between the two tallest rects and place the rest apart
        g = _paint_carve_pair_constructive(h, w, palette, dims, rng)
    if g is None:
        g = _paint_separated(h, w, palette, dims, anchors, rng, bias)
    if g is None:
        g = _paint_bars_fallback(h, w, palette, heights, rng, bias)
    if g is None:
        raise RuntimeError(f"{TASK_ID}: could not place color blocks")
    return g


# ---------------------------------------------------------------------------
# Contract hooks
# ---------------------------------------------------------------------------

def observe_overrides(grid) -> dict:
    """Report the realized per-draw values of the exact semantic axes.

    n_colors counts the distinct non-bg colors; construction guarantees
    every drawn color survives (stacked blocks keep top/bottom cells), so
    the observed count is exact."""
    out: dict = {}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return out
    out["grid_h"] = len(grid)
    out["grid_w"] = len(grid[0])
    out["n_colors"] = len({v for row in grid for v in row if v != 0})
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants for the bbox-height bar-chart task.

    Declared degenerate modes are recognized ONLY as their exact families:
    single_color = one 1-wide vertical bar of one color on an all-zero
    grid; full_grid = a 2-color parity checkerboard with no background;
    tied_heights = all colors sharing one band height. A grid with NO
    non-bg color is always rejected (the rule crashes on the empty color
    list). Normal draws require: unique 0-modal background, every color a
    contiguous row band with one contiguous run per non-empty row, and
    DISTINCT band heights (an all-tied grid is the declared tied mode;
    a partial tie is neither)."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if not (6 <= h <= 19):
        errors.append(f"grid height {h} outside declared envelope 6..19")
    if not (6 <= w <= 20):
        errors.append(f"grid width {w} outside declared envelope 6..20")
    colors = sorted({v for row in grid for v in row})
    if any(not isinstance(v, int) or v < 0 or v > 9 for v in colors):
        errors.append(f"colors outside 0..9: {colors}")
    fg = [c for c in colors if c != 0]
    if not fg:
        errors.append("grid has no non-bg color (the rule crashes on an empty color list)")
        return errors
    if len(fg) == 1:
        # Accept ONLY the exact single_color family: one 1-wide vertical bar
        # of one color, everything else background. Arbitrary one-color
        # shapes (L, blob, horizontal line, monochrome fill) are rejected.
        c0 = fg[0]
        cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == c0]
        cols = {c for _, c in cells}
        rows = [r for r, _ in cells]
        if not (len(cols) == 1 and len(cells) >= 2
                and max(rows) - min(rows) == len(cells) - 1):
            errors.append("single-color grids must be exactly one vertical 1-wide bar (declared single_color family)")
        return errors
    if 0 not in colors:
        # Accept ONLY the exact full_grid family: a 2-color parity
        # checkerboard. No-zero monochrome or two-color splits are rejected.
        if len(fg) != 2:
            errors.append("zero-free grids must be exactly the 2-color parity checkerboard (declared full_grid family)")
            return errors
        a, b = fg
        ok = all(grid[r][c] == (a if (r + c) % 2 == 0 else b)
                 for r in range(h) for c in range(w)) or \
             all(grid[r][c] == (b if (r + c) % 2 == 0 else a)
                 for r in range(h) for c in range(w))
        if not ok:
            errors.append("zero-free grids must be exactly the 2-color parity checkerboard (declared full_grid family)")
        return errors
    # --- every color must be a contiguous row band with contiguous runs ---
    bands = _color_bands(grid)
    struct_ok = True
    for color in fg:
        lo, hi, _ht = bands[color]
        if not _color_structure_ok(grid, color, lo, hi):
            struct_ok = False
            errors.append(f"color {color} does not form one contiguous run per band row")
            break
    # --- background prior (normal + tied modes are sparse) ------------------
    counts = {v: sum(row.count(v) for row in grid) for v in colors}
    if counts.get(0, 0) <= max((v for k, v in counts.items() if k != 0), default=0):
        errors.append("background color 0 must be the unique modal color")
    # --- band heights: DISTINCT on normal draws. tied_heights is a declared
    # mode in which ALL colors share one height; a partial tie is neither. ---
    if struct_ok:
        heights = [ht for (_lo, _hi, ht) in bands.values()]
        if len(set(heights)) != 1 and len(set(heights)) != len(heights):
            errors.append("band heights must be all-distinct (normal) or all-tied (declared tied_heights mode)")
    return errors


# ---------------------------------------------------------------------------
# Executable semantic contract
# ---------------------------------------------------------------------------

def _bbox_stats(grid):
    """Racket ``grid-colors`` order with each nonzero color's bbox dimensions."""
    bounds = {}
    for row_index, row in enumerate(grid):
        for col_index, color in enumerate(row):
            if color == 0:
                continue
            if color not in bounds:
                bounds[color] = [row_index, row_index, col_index, col_index]
            else:
                box = bounds[color]
                box[0] = min(box[0], row_index)
                box[1] = max(box[1], row_index)
                box[2] = min(box[2], col_index)
                box[3] = max(box[3], col_index)
    return [
        (color, bounds[color][1] - bounds[color][0] + 1,
         bounds[color][3] - bounds[color][2] + 1)
        for color in sorted(bounds)
    ]


def _render_measurements(measurements, *, descending, top_aligned):
    """Render ``(amount, color)`` pairs as the task's compact bar chart."""
    ordered = sorted(measurements, key=lambda item: item[0], reverse=descending)
    if not ordered:
        return []
    maximum = max(amount for amount, _color in ordered)
    out = full_grid(maximum, len(ordered), 0)
    for col_index, (amount, color) in enumerate(ordered):
        first_row = 0 if top_aligned else maximum - amount
        for row_index in range(first_row, first_row + amount):
            out[row_index][col_index] = color
    return out


def rule_mirror(grid):
    """Independent Python mirror of the selected canonical Racket rule."""
    return _render_measurements(
        [(height, color) for color, height, _width in _bbox_stats(grid)],
        descending=True,
        top_aligned=True,
    )


def _rival_sort_ascending(grid):
    return _render_measurements(
        [(height, color) for color, height, _width in _bbox_stats(grid)],
        descending=False,
        top_aligned=True,
    )


def _rival_bbox_width(grid):
    return _render_measurements(
        [(width, color) for color, _height, width in _bbox_stats(grid)],
        descending=True,
        top_aligned=True,
    )


def _rival_bottom_aligned(grid):
    return _render_measurements(
        [(height, color) for color, height, _width in _bbox_stats(grid)],
        descending=True,
        top_aligned=False,
    )


def strict_canonical_like(grid):
    """Accept the ordinary distinct-height teaching manifold, not degenerates."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    stats = _bbox_stats(grid)
    if 0 not in {value for row in grid for value in row}:
        reasons.append("ordinary examples retain background color 0")
    if not 2 <= len(stats) <= 5:
        reasons.append("ordinary examples contain 2..5 nonzero colors")
    heights = [height for _color, height, _width in stats]
    if len(set(heights)) != len(heights):
        reasons.append("ordinary examples use distinct bbox heights")
    return reasons


def _witness_descending_order(grid):
    heights = [height for _color, height, _width in _bbox_stats(grid)]
    return len(set(heights)) >= 2


def _witness_height_not_width(grid):
    return rule_mirror(grid) != _rival_bbox_width(grid)


def _witness_top_alignment(grid):
    heights = [height for _color, height, _width in _bbox_stats(grid)]
    return bool(heights) and min(heights) < max(heights)


# Deliberately wrong programs used to test whether generated lessons actually
# distinguish the measured axis, sort direction, and vertical alignment.
SEMANTIC_RIVALS = {
    "sort_ascending": _rival_sort_ascending,
    "bbox_width": _rival_bbox_width,
    "bottom_aligned": _rival_bottom_aligned,
}
SEMANTIC_WITNESSES = {
    "descending_order": _witness_descending_order,
    "height_not_width": _witness_height_not_width,
    "top_alignment": _witness_top_alignment,
}
WITNESS_RIVALS = {
    "descending_order": ["sort_ascending"],
    "height_not_width": ["bbox_width"],
    "top_alignment": ["bottom_aligned"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
