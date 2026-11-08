"""Generator for dc3b5c670093 (ARC task 762cd429).

Rule: the input is a 0-background grid whose only nonzero cells are a 2x2
TEMPLATE at rows (tr, tr+1), columns 0..1, with arbitrary non-zero colors
(repeats allowed — canonical templates repeat colors).  The output builds a
doubling staircase rightward: step k = 0,1,2,... occupies the next
2^(k+1) columns (2, 4, 8, ...) and spans rows (tr - 2^k + 1)..(tr + 2^k),
tiled as 2x2 macro-quadrants matching the template.

Canonical law (all 7 official pairs): the template is vertically centered
(h = 2*(tr+1)) and the width exactly fills the staircase
(w = 2+4+...+2^(K+1) = 2^(K+2)-2): the two official configurations are
10x14 with tr=4 (K=1) and 16x30 with tr=7 (K=2).

Combinatorial axes (5): grid_h, grid_w, template_row, n_colors (distinct
colors in the template, 2..4), official_size (one of the two official
configurations vs generalized geometry).

Branches exercised: both official configurations (canonical prior),
centered vs off-center templates, exact-fill vs clipped staircase widths,
templates with repeated colors (a==b, b==d, d==e classes) vs all-distinct.

Degenerate textures: none.  A missing/zero template crashes the oracle's
min-of on an empty nonzero list, and a monochrome or all-column template
makes the recovered quadrants ill-defined, so no texture axis is declared
(KRF-0001).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc3b5c670093"
VERSION = "3.0.0"  # canonical-domain rebuild: official 10x14/16x30 centered
# configurations as the dominant prior (was fixed h=9, tr in [3,5], forced
# 4-distinct palette); repeated-color templates, exact envelope self_check.
TASK_ID = "dc3b5c670093"
RULE_HASH = "dc5d69bcdd26"
SUMMARY = (
    "2x2 color template at columns 0..1, vertically centered; output is "
    "the exponentially doubling staircase (block widths 2,4,8,16) built "
    "rightward from the template's quadrants."
)

INVARIANTS = [
    "background is 0; the only nonzero cells are the 2x2 template",
    "the template sits at columns 0..1, rows tr..tr+1 with 1 <= tr <= h-2, "
    "all four cells nonzero (colors may repeat)",
    "declared envelope: h in 8..18, w in 6..30",
    "official configurations (dominant prior): 10x14 tr=4 and 16x30 tr=7, "
    "template vertically centered, width exactly filling the staircase",
]

PALETTE_KINDS: tuple = ()
DEGENERATE_TEXTURES: tuple = ()
HELPFUL_TEXTURES: tuple = ()

AXES = {
    "grid_h":       {"type": "int", "default": "official prior / band rng",
                     "valid": "8..18"},
    "grid_w":       {"type": "int", "default": "official prior / band rng",
                     "valid": "6..30"},
    "template_row": {"type": "int", "default": "centered (h/2-1 even h)",
                     "valid": "1..16"},
    "n_colors":     {"type": "int", "default": "band rng 2..4 (distinct "
                     "colors in the template)", "valid": "2..4"},
    "official_size": {"type": "bool",
                      "default": "rng p(band 0.6..0.7) true (one of the two "
                                 "official 10x14/16x30 configurations)",
                      "valid": "true|false"},
}

_H_LO, _H_HI = 8, 18
_W_LO, _W_HI = 6, 30
_TR_LO, _TR_HI = 1, 16
_NC_LO, _NC_HI = 2, 4
_OFFICIAL = ((10, 14, 4), (16, 30, 7))
_EXACT_W = (6, 14, 30)          # 2^(K+2)-2 for K = 0..2


def _template(grid):
    """Locate the 2x2 template: returns (errs, (tr, colors)) where colors is
    the 2x2 block's values, or (errs, None)."""
    h, w = len(grid), len(grid[0])
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        return ["no nonzero template cells"], None
    tr = min(r for r, _ in nz)
    errs = []
    expected = {(tr, 0), (tr, 1), (tr + 1, 0), (tr + 1, 1)}
    if set(nz) != expected:
        errs.append(
            f"nonzero cells are not exactly a 2x2 template at columns 0..1 "
            f"(found {len(nz)} cells)")
    if tr + 1 >= h:
        errs.append(f"template row {tr} leaves no room for row {tr + 1}")
    if tr < 1:
        errs.append(f"template row {tr} outside declared 1..16 envelope")
    if tr > 16:
        errs.append(f"template row {tr} outside declared 1..16 envelope")
    if errs:
        return errs, None
    colors = [grid[tr][0], grid[tr][1], grid[tr + 1][0], grid[tr + 1][1]]
    if len(set(colors)) < 2:
        errs.append(
            "monochrome template: declared n_colors is 2..4 distinct colors")
    return errs, None if errs else (tr, colors)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular 0..9 grid in
    the declared envelope (h 8..18, w 6..30) whose only nonzero cells are a
    2x2 all-nonzero template at columns 0..1 with template row in 1..16.
    An empty template crashes the oracle's min-of, a template off columns
    0..1 corrupts its quadrant read, and off-envelope sizes are rejected;
    grids already containing staircase blocks (outputs) are rejected too."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if not (_H_LO <= h <= _H_HI) or not (_W_LO <= w <= _W_HI):
        errs.append(
            f"grid {h}x{w} outside declared {_H_LO}..{_H_HI} x "
            f"{_W_LO}..{_W_HI} envelope")
    if any(not 0 <= v <= 9 for row in grid for v in row):
        errs.append("color outside 0..9")
    terrs, _info = _template(grid)
    errs.extend(terrs)
    return errs


def observe_overrides(grid):
    """Realized per-draw values of the exact semantic axes (KRF-0002):
    template row, distinct template colors, official-config flag — all
    derived from the grid itself."""
    errs, info = _template(grid)
    if errs or info is None:
        return {}
    tr, colors = info
    h, w = len(grid), len(grid[0])
    return {"grid_h": h, "grid_w": w, "template_row": tr,
            "n_colors": len(set(colors)),
            "official_size": (h, w, tr) in _OFFICIAL}


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; overrides validated against the full valid
    range (an override must execute on any band, per the AXES contract)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _template_colors(rng, n_colors):
    """n_colors distinct colors from 1..9, all used across the 4 template
    cells (canonical templates repeat colors)."""
    pool = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_colors)
    slots = pool + [pool[rng.randrange(n_colors)]
                    for _ in range(4 - n_colors)]
    rng.shuffle(slots)
    return slots


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = dict(overrides)
    if overrides.get("official_size") is not None:
        raw = overrides["official_size"]
        overrides["official_size"] = (raw if isinstance(raw, bool)
                                      else str(raw).strip().lower()
                                      in ("1", "true", "yes"))
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    band = difficulty or "medium"
    if band == "easy":
        h_opts, w_opts, off_p, ncs, p_off = \
            [8, 10, 12], [6, 10, 14], 0.0, (3, 4), 0.7
    elif band == "hard":
        h_opts, w_opts, off_p, ncs, p_off = \
            [10, 12, 14, 16, 18], list(range(12, 31, 2)), 0.5, (2, 3, 4), 0.6
    else:
        h_opts, w_opts, off_p, ncs, p_off = \
            [10, 12, 14, 16], list(range(10, 25, 2)), 0.0, (2, 3, 4), 0.65

    h_pinned = "grid_h" in overrides and overrides["grid_h"] is not None
    w_pinned = "grid_w" in overrides and overrides["grid_w"] is not None
    tr_pinned = ("template_row" in overrides and
                 overrides["template_row"] is not None)
    rng = ctx.draw_rng("layout")
    # Exact pinned dimensions outrank a random official_size draw: they can
    # only combine with an official configuration they are compatible with.
    compat = [cfg for cfg in _OFFICIAL
              if (not h_pinned or cfg[0] == overrides["grid_h"])
              and (not w_pinned or cfg[1] == overrides["grid_w"])
              and (not tr_pinned or cfg[2] == overrides["template_row"])]
    if "official_size" in overrides and overrides["official_size"] is not None:
        official = ctx.draw_choice("official_size", [False, True])
        if official and not compat:
            raise ValueError(
                "official_size=True conflicts with pinned "
                f"grid_h={overrides.get('grid_h')}, "
                f"grid_w={overrides.get('grid_w')}, "
                f"template_row={overrides.get('template_row')}: no official "
                f"configuration matches {sorted(_OFFICIAL)}")
    else:
        official = bool(compat) and ctx.draw_rng("official_size").random() < p_off

    if official:
        h, w, tr = compat[rng.randrange(len(compat))]
        h = ctx.draw_int("grid_h", h, h)
        w = ctx.draw_int("grid_w", w, w)
        tr = ctx.draw_int("template_row", tr, tr)
    else:
        if h_pinned:
            h = ctx.draw_int("grid_h", _H_LO, _H_HI)
        else:
            h = ctx.draw_choice("grid_h", list(h_opts))
        if w_pinned:
            w = ctx.draw_int("grid_w", _W_LO, _W_HI)
        else:
            w = ctx.draw_choice("grid_w", list(w_opts))
        # template_row: exact when pinned (grid grows around it when the
        # height itself was not requested), else centered (off-center share
        # on hard as documented generalization).
        if tr_pinned:
            tr = ctx.draw_int("template_row", _TR_LO, _TR_HI)
            if tr + 1 > h - 1:
                if h_pinned:
                    raise ValueError(
                        f"template_row={tr} needs grid_h >= {tr + 2}; exact "
                        f"grid_h={h} was requested")
                h = min(_H_HI, tr + 2)
        else:
            mid = h // 2 - 1 if h % 2 == 0 else (h - 1) // 2 - 1
            mid = max(1, mid)
            if off_p > 0 and rng.random() < off_p:
                tr = rng.randint(1, h - 2)
            else:
                tr = mid
        # official_size=False is exact: never land on an official config;
        # nudge an unpinned dimension, reject when every dim is pinned.
        if (h, w, tr) in _OFFICIAL:
            nudged = False
            if not w_pinned:
                alts = [x for x in w_opts
                        if (h, x, tr) not in _OFFICIAL and x != w]
                if alts:
                    w = alts[rng.randrange(len(alts))]
                    nudged = True
            if not nudged and not h_pinned:
                alts = [x for x in h_opts
                        if (x, w, tr) not in _OFFICIAL and x != h]
                if alts:
                    h = alts[rng.randrange(len(alts))]
                    nudged = True
            if not nudged and not tr_pinned:
                tr2 = tr + 1 if tr + 1 <= h - 2 else tr - 1
                if (h, w, tr2) not in _OFFICIAL:
                    tr = tr2
                    nudged = True
            if not nudged:
                raise ValueError(
                    f"pinned dims (grid_h={h}, grid_w={w}, "
                    f"template_row={tr}) force an official configuration "
                    f"while official_size=False was requested")
    n_colors = _banded_int(ctx, overrides, "n_colors",
                           min(ncs), max(ncs), _NC_LO, _NC_HI)
    colors = _template_colors(rng, n_colors)
    g = full_grid(h, w, 0)
    g[tr][0] = colors[0]
    g[tr][1] = colors[1]
    g[tr + 1][0] = colors[2]
    g[tr + 1][1] = colors[3]
    return g
