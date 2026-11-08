"""Generator for arc_puzzle_bank_21_set16_bundle:easy_p06.

Rule: each column retains only its bottommost nonzero cell.

Combinatorial axes (8): grid_h, grid_w, palette_kind, column_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_singleton_cols, all_at_bottom_row, dense_columns.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bc17775383d3"
# 2.2.0: add executable column-collapse self-check.
# 2.1.0: enforce the claimed invariant "at least one active column has
# multiple non-zero cells" (so the collapse is always observable), and
# widen grid/column ranges. Was already diverse; this makes it honest.
VERSION = "2.2.0"
TASK_ID = "bc17775383d3"
SUMMARY = (
    "0-bg grid (h, w ~7-10) with 3-5 ACTIVE COLUMNS, each "
    "containing 1-4 non-zero cells at random rows in "
    "rotating colors from a 6-color palette. At least one "
    "column has multiple non-zero cells. Other columns are "
    "fully zero. Rule: for each column c, find all non-zero "
    "cells in that column; keep only the one with the "
    "LARGEST r (bottommost) — clear every other non-zero "
    "cell in that column to 0. Net: each column collapses "
    "to at most one cell, located at the bottommost row "
    "where it originally had a value."
)

INVARIANTS = [
    "background is 0",
    "active columns contain one to four nonzero cells",
    "at least one active column has multiple nonzero cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_singleton_cols", "all_at_bottom_row", "dense_columns")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "column_count":   {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "6", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "stacked_columns",
                       "valid": "stacked_columns"},
    "n_distinct_colors": {"type": "int", "default": "6", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        column_count = min(ctx.draw_int("column_count", 2, 3), w)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 10, 14)
        column_count = min(ctx.draw_int("column_count", 5, 7), w)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 7, 12)
        column_count = min(ctx.draw_int("column_count", 3, 6), w)
    colors = ctx.draw_distinct_colors("colors", n=6, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    cols = rng.sample(range(w), column_count)
    # Force at least one column to have >=2 cells so the collapse is visible.
    multi_col = rng.choice(cols)
    for i, c in enumerate(cols):
        if c == multi_col:
            n = rng.randint(2, min(4, h))
        else:
            n = rng.randint(1, min(4, h))
        rows = rng.sample(range(h), n)
        for j, r in enumerate(rows):
            g[r][c] = colors[(i + j) % len(colors)]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "all_singleton_cols":
        # every active column has exactly one cell → "bottommost" is that cell, rule is identity
        g[2][1] = 4; g[5][3] = 6; g[3][6] = 3; g[1][7] = 8
        return g
    if name == "all_at_bottom_row":
        # all active cells already on the bottom row → rule is identity
        g[h - 1][1] = 4; g[h - 1][3] = 6; g[h - 1][5] = 3; g[h - 1][7] = 8
        return g
    if name == "dense_columns":
        # columns are completely filled → rule keeps only the bottom row, output collapses by ~h
        for r in range(h):
            for c in [2, 5, 7]:
                g[r][c] = (r % 8) + 1
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    h = len(grid); w = len(grid[0]) if h else 0
    active = []
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] != 0]
        if rows:
            active.append((c, rows))
            if len(rows) > 4:
                msgs.append("active columns should contain at most four cells")
    if not active:
        msgs.append("expected active columns")
    if not any(len(rows) >= 2 for _, rows in active):
        msgs.append("at least one active column must have multiple cells")
    return msgs
