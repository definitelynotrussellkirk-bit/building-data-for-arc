"""Generator for arc_puzzle_bank_twentythird21:H160.

Replay accent-color stencil positions from A->B onto same-support C.

Combinatorial axes (8): grid_h, grid_w, palette_kind, variant,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_accent, mismatched_supports, panel_c_already_full.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "170ec3daa52f"
# 1.2.0: was a fixed 4x14 grid, full 4x4 support, 3 fixed accent patterns
#        (shape-locked in+out, dup-outputs). Now randomize panel rows/cols
#        (so crop/output shape varies) and the accent cell set (any 1-4
#        support cells); all 3 panels share the same full support.
VERSION = "1.2.1"
TASK_ID = "170ec3daa52f"
SUMMARY = "Replay accent-color stencil positions from A->B onto same-support C."

INVARIANTS = [
    "the input has three 4x4 panels separated by full color-8 columns",
    "all panels have the same nonzero support",
    "panel B recolors a few supported cells with one accent color",
    "panel C keeps its base color except at those accent stencil positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_accent", "mismatched_supports", "panel_c_already_full")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "4", "valid": "4..4"},
    "grid_w":         {"type": "int", "default": "14", "valid": "14..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "variant":        {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "three_panels_separated_by_8",
                       "valid": "three_panels_separated_by_8"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "dense", "valid": "dense"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SUPPORT = {(r, c) for r in range(4) for c in range(4)}
_ACCENTS = [
    [(0, 1), (2, 3)],
    [(1, 0), (1, 2), (3, 2)],
    [(0, 0), (2, 1)],
]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 4-row grid, color-8 column separators present, three panels."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_accent", "mismatched_supports", "panel_c_already_full"):
        return errs
    # The panels are separated by full color-8 columns at cols 4 and 9.
    sep_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(sep_cols) < 2:
        errs.append(f"expected ≥2 full color-8 separator columns, found {len(sep_cols)}")
    return errs


def _paint_panel(g, panel, base_color, accents=(), accent_color=0):
    left = panel * 5
    accent_set = set(accents)
    for r, c in _SUPPORT:
        g[r][left + c] = accent_color if (r, c) in accent_set else base_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        ph, pw = rng.randint(3, 4), rng.randint(3, 4)
        n_accent = rng.randint(1, 2)
    elif difficulty == "hard":
        ph, pw = rng.randint(4, 7), rng.randint(4, 7)
        n_accent = rng.randint(2, 5)
    else:
        ph, pw = rng.randint(3, 6), rng.randint(3, 6)
        n_accent = rng.randint(1, 4)

    # distinct colors: base for A/B, accent (differs from base), base for C
    base_a = rng.choice([1, 2, 3, 4])
    accent = rng.choice([c for c in [6, 7, 9] if c != base_a] or [6])
    base_c = rng.choice([c for c in [5, 6, 7, 9] if c != accent] or [5])

    # All 3 panels: full ph x pw support so crop dims match (output is ph x pw).
    support = [(r, c) for r in range(ph) for c in range(pw)]
    # Accent cells: a random subset of support; keep the bbox extremes filled
    # with NON-accent so crop dims stay ph x pw (corners are base).
    candidate = [p for p in support
                 if p not in {(0, 0), (0, pw - 1), (ph - 1, 0), (ph - 1, pw - 1)}]
    rng.shuffle(candidate)
    accents = candidate[:min(n_accent, len(candidate))]

    # Grid: 3 panels of width pw separated by single full-8 columns.
    w = pw * 3 + 2
    g = full_grid(ph, w, 0)
    sep_cols = (pw, pw * 2 + 1)
    for sep in sep_cols:
        for r in range(ph):
            g[r][sep] = 8

    def _paint(panel_idx, base, acc=(), acc_color=0):
        left = panel_idx * (pw + 1)
        acc_set = set(acc)
        for (r, c) in support:
            g[r][left + c] = acc_color if (r, c) in acc_set else base

    _paint(0, base_a)
    _paint(1, base_a, accents, accent)
    _paint(2, base_c)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(4, 14, 0)
    for sep in (4, 9):
        for r in range(4):
            g[r][sep] = 8
    if name == "no_accent":
        # panels A and B identical → no accent stencil to replay onto C
        _paint_panel(g, 0, 3)
        _paint_panel(g, 1, 3)
        _paint_panel(g, 2, 6)
        return g
    if name == "mismatched_supports":
        # panel C support differs from A/B → "same support" precondition fails
        _paint_panel(g, 0, 3)
        _paint_panel(g, 1, 3, _ACCENTS[0], 7)
        for r in range(4):
            g[r][10] = 6  # only one column on panel C
        return g
    if name == "panel_c_already_full":
        # panel C already has accent everywhere → rule's "stencil onto C" trivial
        _paint_panel(g, 0, 3)
        _paint_panel(g, 1, 3, _ACCENTS[0], 7)
        for r in range(4):
            for c in range(4):
                g[r][10 + c] = 7
        return g
    return g
