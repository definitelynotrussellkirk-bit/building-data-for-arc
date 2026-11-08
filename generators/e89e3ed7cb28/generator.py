"""Generator for arc_puzzle_bank_21_set24_bundle:easy_p04.

Rule: each active column keeps only its bottommost nonzero cell.

Combinatorial axes (8): grid_h, grid_w, palette_kind, column_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, single_per_column, full_columns.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e89e3ed7cb28"
VERSION = "2.1.0"  # clean; widen grids/columns/stack-depth by difficulty (hard: taller grids, deeper stacks 2-6, more columns) for more pruning variety
TASK_ID = "e89e3ed7cb28"
SUMMARY = (
    "0-bg grid (h~7-10, w~8-12) with 4-7 ACTIVE "
    "COLUMNS. Each active column contains 1-3 non-bg "
    "cells stacked vertically at random rows, in "
    "distinct non-bg colors per cell. Other columns "
    "are empty. Rule: for each column, find the "
    "BOTTOMMOST non-zero cell (the cell at the "
    "largest row index in that column). KEEP only "
    "that bottommost cell; erase all other non-zero "
    "cells in the same column to 0. Empty columns "
    "stay empty. Net: gravity-prune — each active "
    "column drops its upper cells and retains only "
    "the lowest one (the bottommost color survives, "
    "others vanish)."
)

INVARIANTS = [
    "background is 0",
    "active columns contain one to three nonzero cells",
    "at most one bottommost cell is selected per column",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_grid", "single_per_column", "full_columns")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "column_count":   {"type": "int", "default": "rng 4..7", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 4..9", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "columns", "valid": "columns"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..9", "valid": "1..9"},
    "density":        {"type": "str", "default": "stacked", "valid": "stacked"},
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
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        column_count = min(ctx.draw_int("column_count", 3, 5), w)
        cmax = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        column_count = min(ctx.draw_int("column_count", 6, 10), w)
        cmax = 6
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 13)
        column_count = min(ctx.draw_int("column_count", 4, 7), w)
        cmax = 4
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    cols = rng.sample(range(w), column_count)

    for c in cols:
        count = rng.randint(1, min(cmax, h))
        rows = sorted(rng.sample(range(h), count))
        # distinct non-bg colors per cell (palette has 9 < deep stacks -> allow repeats)
        if count <= 9:
            colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], count)
        else:
            colors = [rng.randint(1, 9) for _ in range(count)]
        for r, color in zip(rows, colors):
            grid[r][c] = color
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # no active columns → rule has no input to filter
        return g
    if name == "single_per_column":
        # every active column already has just one cell → "bottommost" reduces to identity
        for c, r, v in [(1, 3, 4), (4, 5, 7), (7, 2, 9), (9, 6, 3)]:
            g[r][c] = v
        return g
    if name == "full_columns":
        # active columns are entirely filled with one color → bottommost equals every cell,
        # rule erases all but the last row
        for c in [2, 5, 8]:
            color = (c % 4) + 3
            for r in range(h):
                g[r][c] = color
        return g
    return g
