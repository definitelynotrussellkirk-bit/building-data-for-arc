"""Generator for arc_additional_puzzles_21_set2:E13.

Rule: each col with exactly 2 cells of color 7 separated by all-0 →
fill between them with 4.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, adjacent_7s, more_than_two_7s_per_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3ecae1984445"
VERSION = "2.1.0"  # FIX identity_demo (5/18): active columns only got a 7-pair IF the random rows happened to be >=3 apart, else no 7s placed; when every sampled column drew close rows there was no fillable pair -> rule fills nothing -> output==input. Now place a guaranteed >=2-gap pair in each interior active column (distractor edges 0/w-1 kept separate). + self_check.
TASK_ID = "3ecae1984445"
SUMMARY = (
    "0-bg grid (h~5-7, w~"
    "6-8) with: (a) 2-3 "
    "ACTIVE COLUMNS each "
    "containing EXACTLY 2 "
    "ORANGE(7) CELLS at "
    "distinct rows "
    "separated by ≥2 "
    "ZEROES between (so "
    "they're not adjacent); "
    "(b) ONE DISTRACTOR "
    "ROW with two 7s at "
    "the LEFT and RIGHT "
    "edge of an otherwise "
    "empty row. Rule (PER "
    "COLUMN, FILL BETWEEN "
    "TWO 7-CELLS WITH "
    "YELLOW 4): For EACH "
    "COLUMN c: count cells "
    "with color 7. If "
    "exactly 2 and "
    "separated by all-0 "
    "cells between: PAINT "
    "every cell strictly "
    "BETWEEN them in "
    "column c with COLOR "
    "4 (yellow). The two "
    "7-endpoints stay. "
    "Columns with !=2 7s "
    "or adjacent pairs "
    "(distractor row) are "
    "LEFT UNCHANGED. Net: "
    "valid column-pairs "
    "bridge with yellow; "
    "row distractors "
    "remain untouched."
)

INVARIANTS = [
    "≥2 cols have exactly 2 cells of color 7 with ≥2 0-cells between",
    "≥1 distractor row of two 7s adjacent (won't fill)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "adjacent_7s", "more_than_two_7s_per_col")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "column_pairs",
                       "valid": "column_pairs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
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
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 6, 8)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    # Active columns are INTERIOR (1..w-2) so they never collide with the
    # distractor row's edge-7s at columns 0 and w-1 (which would give those
    # columns a 3rd 7 and disqualify the pair).
    interior = list(range(1, w - 1))
    k = min(rng.randint(2, 3), len(interior))
    cols = rng.sample(interior, k)
    for c in cols:
        # Guarantee a fillable pair: rows >=3 apart (>=2 zero cells between).
        r1 = rng.randint(0, h - 4)
        r2 = rng.randint(r1 + 3, h - 1)
        g[r1][c] = 7
        g[r2][c] = 7
    # Distractor row: two 7s at the left/right edges of an empty row (same
    # row -> each is alone in its column -> never filled).
    empties = [r for r in range(h) if all(g[r][c2] == 0 for c2 in range(w))]
    if empties:
        r_dec = rng.choice(empties)
        g[r_dec][0] = 7
        g[r_dec][w - 1] = 7
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """At least one column must have exactly two 7s separated by all-0 cells
    (a fillable pair), so the rule paints >=1 cell (output != input).
    Returns a list of violations (empty == pass)."""
    h, w = len(grid), len(grid[0])
    fillable = 0
    for c in range(w):
        hits = [r for r in range(h) if grid[r][c] == 7]
        if len(hits) == 2 and hits[1] - hits[0] >= 2 \
                and all(grid[r][c] == 0 for r in range(hits[0] + 1, hits[1])):
            fillable += 1
    if fillable == 0:
        return ["no column has a fillable 7-pair -> rule paints nothing"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # only singletons of 7 → no col-pair to bridge
        g[1][2] = 7
        g[3][5] = 7
        return g
    if name == "adjacent_7s":
        # vertical pair of 7s touching → no gap to fill
        g[1][2] = 7; g[2][2] = 7
        g[4][5] = 7; g[5][5] = 7
        return g
    if name == "more_than_two_7s_per_col":
        # column has 3+ 7-cells → which pair to bridge ambiguous
        g[0][3] = 7; g[3][3] = 7; g[6][3] = 7
        return g
    return g
