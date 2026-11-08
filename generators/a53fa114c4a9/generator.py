"""Generator for arc_puzzle_bank_fifth21:H35.

Rows 0 and 1 define a color map, row 2 defines a column mask, and the body is
recolored then cropped to the marked columns.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_mask, blank_body.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a53fa114c4a9"
VERSION = "2.1.2"  # align advertised n_pairs range with the 8-color legend budget
TASK_ID = "a53fa114c4a9"
SUMMARY = (
    "0-bg grid (h~8-13, w~10-17) with "
    "STRUCTURED LAYOUT: (a) ROWS 0 and 1 — "
    "LEGEND: at n_pairs (2-4) DISTINCT "
    "COLUMNS, row 0 holds a SOURCE COLOR "
    "and row 1 holds the corresponding "
    "TARGET COLOR (aligned src→dst pairs). "
    "Source/target colors are drawn from "
    "{2..9} as 2 * n_pairs distinct values. "
    "Other cells in rows 0-1 are bg-0; (b) "
    "ROW 2 — COLUMN-KEEP MASK: at n_keep "
    "(2-8) DISTINCT COLUMNS, paint cells "
    "with COLOR 1 (the mask marker). Other "
    "cells in row 2 are bg-0; (c) ROWS 3..h-"
    "1 — BODY: each body cell is "
    "INDEPENDENTLY filled with a random "
    "SRC color (from the legend) at "
    "density 0.42, plus guaranteed "
    "source cells at each (keep_col[i], "
    "3 + (i % (h-3))) position. Rule "
    "(RECOLOR BODY VIA LEGEND THEN CROP "
    "TO MASK-MARKED COLUMNS): READ the "
    "LEGEND (rows 0-1) to build a SRC→DST "
    "color map. APPLY the map to every "
    "cell in the BODY (rows 3..h-1): each "
    "SRC-color cell becomes its DST. READ "
    "the MASK (row 2) — get the LIST of "
    "KEEP COLUMNS (cells where g[2][c]=1). "
    "CROP the recolored body to only "
    "those columns. OUTPUT is (h-3) rows "
    "× n_keep cols (legend and mask rows "
    "are discarded). Net: a recoloring "
    "filter applied to the body, then a "
    "column-subset crop."
)

# Rivals: 'crop without recolor' refuted by ≥1 demo where body cells
# clearly changed color. 'recolor without crop' refuted by any demo
# where output is narrower than input. 'keep all columns' refuted by
# ≥2 demos where output is narrower. 'use mask row as content'
# refuted by any demo (output rows = body rows).
# 4 demos with varied legends + masks cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "rows 0 and 1 contain aligned source/target color pairs",
    "row 2 contains the color-1 keep-column mask",
    "body rows begin at row 3",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_mask", "blank_body")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "10", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "13", "valid": "10..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "2..4"},
    "n_keep":         {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 4..8", "valid": "4..10"},
    "position_bias":  {"type": "str", "default": "legend_mask_body",
                       "valid": "legend_mask_body"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..8", "valid": "4..10"},
    "density":        {"type": "str", "default": "dense", "valid": "dense"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_legend|no_mask|blank_body"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rows 0-1 form a legend with paired src/dst colors at matching columns;
    row 2 has color-1 mask markers; rows 3+ form the body."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h < 4:
        return []
    errs = []
    # Row 0: legend sources; row 1: targets (both non-zero at same cols, 0 elsewhere)
    row0_nz = [c for c in range(w) if grid[0][c] != 0]
    row1_nz = [c for c in range(w) if grid[1][c] != 0]
    if not row0_nz:
        errs.append("row 0 has no legend source cells")
    if row0_nz != row1_nz:
        errs.append(f"legend rows 0/1 differ in non-zero columns")
    # Row 2: color-1 mask cells
    mask_cells = [c for c in range(w) if grid[2][c] == 1]
    if not mask_cells:
        errs.append("row 2 has no color-1 mask cells")
    # Body (rows 3+) should have some non-bg cells
    body_nz = sum(1 for r in range(3, h) for c in range(w) if grid[r][c] != 0)
    if body_nz == 0:
        errs.append("body (rows 3+) has no non-bg cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 13)
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
        n_keep = ctx.draw_int("n_keep", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 16, 22)
        n_pairs = ctx.draw_int("n_pairs", 3, 4)
        n_keep = ctx.draw_int("n_keep", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 17)
        n_pairs = ctx.draw_int("n_pairs", 2, 4)
        n_keep = ctx.draw_int("n_keep", 3, 6)
    # Constrain by grid width
    n_pairs = min(n_pairs, max(2, w // 3))
    # The legend draws 2*n_pairs DISTINCT colors from {2..9} (8 values), so
    # n_pairs ≤ 4. Hard's wide grids let w//3 reach 7, so n_pairs could hit 5 →
    # rng.sample(8-list, 10) raised "Sample larger than population". Color budget.
    n_pairs = min(n_pairs, 4)
    n_keep = min(n_keep, w)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], n_pairs * 2)
    srcs = colors[:n_pairs]
    dsts = colors[n_pairs:]
    pair_cols = sorted(rng.sample(range(w), n_pairs))
    keep_cols = sorted(rng.sample(range(w), n_keep))
    g = full_grid(h, w, 0)
    for c, src, dst in zip(pair_cols, srcs, dsts):
        g[0][c] = src
        g[1][c] = dst
    for c in keep_cols:
        g[2][c] = 1
    for r in range(3, h):
        for c in range(w):
            if rng.random() < 0.42:
                g[r][c] = rng.choice(srcs)
    for i, c in enumerate(keep_cols):
        g[3 + (i % (h - 3))][c] = srcs[i % len(srcs)]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # mask + body but no row-0/1 legend → no recolor mapping defined
        for c in [2, 5, 8]: g[2][c] = 1
        for r in range(3, h):
            for c in range(w):
                if (r + c) % 3 == 0: g[r][c] = 4
        return g
    if name == "no_mask":
        # legend + body but no row-2 mask → no columns to keep
        g[0][2] = 4; g[1][2] = 6
        for r in range(3, h):
            for c in range(w):
                if (r + c) % 3 == 0: g[r][c] = 4
        return g
    if name == "blank_body":
        # legend + mask but body all-zero → recolor + crop yields blank
        g[0][2] = 4; g[1][2] = 6
        for c in [2, 5, 8]: g[2][c] = 1
        return g
    return g
