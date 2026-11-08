"""Generator for arc_puzzle_bank_ninth_21_bundle:easy_58_cast_vertical_shadows.

Rule: single colored seeds cast same-color shadows to the bottom row.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seed_at_bottom, two_seeds_same_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f41434442413"
VERSION = "2.0.0"  # bigger grids + more seeds (kept one-seed-per-column to match canonical)
TASK_ID = "f41434442413"
SUMMARY = ("Single colored seeds (one per column, distinct columns) cast same-color "
           "shadows straight down to the bottom row. Grid size and seed count vary; "
           "every seed has >=1 blank cell below. (Was: 7-10 grids, 2-5 seeds.)")

INVARIANTS = [
    "background is 0",
    "each active column contains exactly one seed",
    "seed columns are distinct",
    "every seed has at least one blank cell below it",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seed_at_bottom", "two_seeds_same_col")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seeds":          {"type": "int", "default": "rng 2..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "distinct_cols", "valid": "distinct_cols"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..9"},
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
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 9)
        target = min(ctx.draw_int("seeds", 2, 4), w)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 11, 16)
        target = min(ctx.draw_int("seeds", 5, 9), w)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        target = min(ctx.draw_int("seeds", 3, 6), w)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    columns = rng.sample(range(w), target)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(target, 9))
    for i, c in enumerate(columns):
        r = rng.randint(0, h - 2)
        g[r][c] = colors[i % len(colors)]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # empty grid — no shadows to cast
        return g
    if name == "seed_at_bottom":
        # seed on bottom row → shadow length 0
        g[h - 1][3] = 4
        return g
    if name == "two_seeds_same_col":
        # two seeds share a column → seed-per-column invariant fails
        g[1][4] = 4
        g[3][4] = 6
        return g
    return g
