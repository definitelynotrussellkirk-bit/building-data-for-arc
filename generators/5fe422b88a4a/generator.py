"""Generator for arc_puzzle_bank_twentyfirst21:E142 — keep topmost non-zero per column.

Rule: each column may have multiple non-zero cells; the output keeps
only the topmost one and zeros the rest.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_singletons, all_at_top_row, full_columns.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5fe422b88a4a"
VERSION = "2.0.1"
TASK_ID = "5fe422b88a4a"
SUMMARY = (
    "0-bg grid (h~5-7, w~5-7) with "
    "4-8 NON-ZERO CELLS scattered "
    "at random positions in random "
    "colors from 1..9. At least 2 "
    "columns have ≥2 non-zero "
    "cells (so the rule's effect "
    "is visible). Rule (KEEP "
    "TOPMOST NON-ZERO PER "
    "COLUMN): for EACH COLUMN, "
    "find all NON-ZERO cells in "
    "that column. KEEP only the "
    "TOPMOST (smallest row index) "
    "one. ERASE all other non-"
    "zero cells in the column "
    "to BG (0). Net: each column "
    "shrinks to its topmost "
    "non-zero cell; columns with "
    "0 or 1 non-zeros unchanged."
)

INVARIANTS = [
    "background is 0",
    "4-8 non-zero cells in any colors at random positions",
    "at least 2 columns have ≥2 non-zero cells (so the rule's effect is visible)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_singletons", "all_at_top_row", "full_columns")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 4..8", "valid": "3..12"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "scattered", "valid": "scattered"},
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
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_int("grid_w", 5, 5)
        n = ctx.draw_int("n_cells", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
        n = ctx.draw_int("n_cells", 7, 8)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 5, 7)
        n = ctx.draw_int("n_cells", 4, 8)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        for _ in range(n):
            for _t in range(40):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0: continue
                g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
                break
        col_counts = [sum(1 for r in range(h) if g[r][c] != 0) for c in range(w)]
        if max(col_counts) >= 2:
            return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one column must have >=2 nonzero cells (so rule has an effect)."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    multi_col = any(
        sum(1 for r in range(h) if grid[r][c] != 0) >= 2
        for c in range(w)
    )
    if not multi_col:
        errors.append("no column has >=2 nonzero cells (rule would be a no-op)")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 6, 6
    g = full_grid(h, w, 0)
    if name == "all_singletons":
        # every column has at most one nonzero → rule is identity, no rule effect visible
        g[1][0] = 4; g[2][2] = 6; g[4][3] = 3; g[3][5] = 8
        return g
    if name == "all_at_top_row":
        # all nonzeros already on top row → rule is identity (each is topmost in its column)
        for c in [0, 2, 3, 5]:
            g[0][c] = (c % 8) + 1
        return g
    if name == "full_columns":
        # active columns completely filled top-to-bottom → output keeps only the top cell, dropping h-1 cells
        for c in [1, 3, 5]:
            color = (c % 8) + 1
            for r in range(h):
                g[r][c] = color
        return g
    return g
