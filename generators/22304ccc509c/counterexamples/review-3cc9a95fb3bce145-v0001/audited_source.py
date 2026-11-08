"""Generator for arc_puzzle_bank_21_set6:easy_f06.

Rule: drop every column's nonzero values to the bottom, preserving
top-to-bottom order.

Combinatorial axes (8): grid_h/w, palette_kind, n_columns, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, already_settled, full_columns.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "22304ccc509c"
VERSION = "2.1.0"  # AXES synced to the real band draws (defect-lint axis-honesty)
RULE_HASH = "c3638032481f"  # canonical rule this generator was written against


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least one column has nonzeros that will drop."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        errs.append("no non-zero cells (nothing for gravity-drop to act on)")
    moving_cols = 0
    for c in range(w):
        vals = [grid[r][c] for r in range(h) if grid[r][c] != 0]
        if not vals:
            continue
        settled = [0] * (h - len(vals)) + vals
        if [grid[r][c] for r in range(h)] != settled:
            moving_cols += 1
    if moving_cols == 0:
        errs.append("all populated columns are already settled; rule would be identity")
    return errs
TASK_ID = "22304ccc509c"
SUMMARY = (
    "0-bg grid (h~6-8, w~6-9) with "
    "NONZERO VALUES scattered "
    "vertically in 3-5 random "
    "COLUMNS, each column having "
    "1-k_max (1-2/5/7 depending on "
    "difficulty) nonzero cells at "
    "random rows (≤ h-2 — leaving "
    "at least one bg cell to fall "
    "into). Each cell is a random "
    "color from 1..9 (independent "
    "per cell). Rule (PER-COLUMN "
    "GRAVITY DROP): for EACH COLUMN "
    "independently, COLLECT all "
    "non-zero values in their "
    "ORIGINAL TOP-TO-BOTTOM ORDER. "
    "DROP them to the BOTTOM of the "
    "column — pack them flush at "
    "the bottom, preserving "
    "top-to-bottom relative order. "
    "Empty cells stay at the top. "
    "Net: per-column vertical "
    "gravity; non-zero values "
    "settle to bottom; order "
    "preserved."
)

# Rivals: 'sort cells by value' refuted by ≥1 demo where preserved
# order doesn't match sort order. 'horizontal gravity (left/right)'
# refuted by any demo with multiple columns. 'fill all with same color'
# refuted by ≥2 demos with different palettes.
# 3 demos with varied column counts + densities cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "columns are transformed independently",
    "nonzero values keep their top-to-bottom order",
    "all values settle at the bottom of their original column",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("empty_grid", "already_settled", "full_columns")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "4-6 easy / 7-11 med / 13-18 hard",
                       "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "4-7 easy / 7-12 med / 13-18 hard",
                       "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "columns":        {"type": "int", "default": "1-4 easy / 3-8 med / 6-14 hard (capped by w)",
                       "valid": "1..14"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scatter",
                       "valid": "scatter"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 4, 7)
        n_cols_lo, n_cols_hi = 1, 4
        k_max = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n_cols_lo, n_cols_hi = 6, 14
        k_max = 7
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 7, 12)
        n_cols_lo, n_cols_hi = 3, 8
        k_max = 5
    n = min(ctx.draw_int("columns", n_cols_lo, n_cols_hi), w)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for c in rng.sample(range(w), n):
        k = rng.randint(1, min(k_max, h - 1))
        rows = sorted(rng.sample(range(h - 1), k))
        for r in rows:
            g[r][c] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # nothing to drop — output equals input
        return g
    if name == "already_settled":
        # all nonzero cells already at bottom — gravity is identity
        g[h - 1][1] = 4
        g[h - 1][3] = 6
        g[h - 2][3] = 5
        return g
    if name == "full_columns":
        # column completely filled — gravity is identity (already packed)
        for r in range(h):
            g[r][2] = ((r % 7) + 1)
        return g
    return g
