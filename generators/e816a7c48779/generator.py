"""Generator for arc_puzzle_bank_21_set18_bundle:easy_p01.

Rule: rows with exactly two same-color seeds extend that spacing periodically
to the right.

Combinatorial axes (8): grid_h, grid_w, palette_kind, row_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, single_seed, mismatched_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e816a7c48779"
VERSION = "2.0.0"  # seeds placed randomly in [0,w-step-1] -> ~43% of seed-rows sat too far right to extend (output==input for that row, no visible signal). Now place leftmost seed so >=1 extension cell is guaranteed (c0 <= w-1-2*step)
TASK_ID = "e816a7c48779"
SUMMARY = (
    "0-bg grid; several rows each have exactly two same-color seeds spaced by "
    "`step`, placed left enough that the periodic pattern extends to the right "
    "edge. Rule: a row with exactly two same-color cells gets c0, c0+step, "
    "c0+2*step, ... painted rightward to the edge; other rows unchanged. Every "
    "seed-row extends (>=1 new cell); step, color, position, count and grid vary."
)

INVARIANTS = [
    "background is 0",
    "each active row has exactly two same-color seeds (rest of the row is 0)",
    "the leftmost seed is placed so the pattern extends right (>=1 new cell)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "single_seed", "mismatched_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "row_count":      {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_seed_pairs",
                       "valid": "row_seed_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
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
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 10, 11)
        row_count = min(ctx.draw_int("row_count", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 13, 14)
        row_count = min(ctx.draw_int("row_count", 4, 5), h)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 10, 14)
        row_count = min(ctx.draw_int("row_count", 3, 5), h)
    colors = ctx.draw_distinct_colors("colors", n=row_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), row_count)
    for i, r in enumerate(rows):
        step = rng.randint(2, max(2, min(4, (w - 1) // 2)))
        # place the leftmost seed so >=1 extension cell fits (c0 + 2*step <= w-1)
        c1 = rng.randint(0, max(0, w - 1 - 2 * step))
        c2 = c1 + step
        g[r][c1] = colors[i]
        g[r][c2] = colors[i]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 12
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank → no rows have seeds, rule has no effect
        return g
    if name == "single_seed":
        # rows have only 1 seed each → no pair to extend
        g[1][3] = 4
        g[3][5] = 6
        g[5][7] = 3
        return g
    if name == "mismatched_seeds":
        # rows have 2 seeds but in different colors → predicate "same color" fails
        g[1][1] = 4; g[1][5] = 6
        g[3][2] = 3; g[3][7] = 8
        return g
    return g
