"""Generator for arc_puzzle_bank_21_set2:S2_M4 — header/side intersections.

Rule: top row has 1-marks at certain columns. Left column has 2-marks
at certain rows. Output paints color 4 at every (row, col) cell where
row is a 2-marked row AND col is a 1-marked col.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_top, n_left,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_top_marks, no_left_marks, all_rows_all_cols.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "47c6b843eaf0"
VERSION = "1.1.1"
TASK_ID = "47c6b843eaf0"
SUMMARY = "Top-row 1-markers + left-col 2-markers (with empty (0,0) corner)."

INVARIANTS = [
    "background is 0",
    "(0,0) is 0 (since neither col 0 has a 1 nor row 0 has a 2 there)",
    "row 0 has 1-marks only at cols >= 1; col 0 has 2-marks only at rows >= 1",
    "≥1 1-mark and ≥1 2-mark (so output is non-empty)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_top_marks", "no_left_marks", "all_rows_all_cols")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_top":          {"type": "int", "default": "rng 2..3", "valid": "0..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "border_marks",
                       "valid": "border_marks"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
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
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    n_1 = rng.randint(2, 3)
    n_2 = rng.randint(2, 3)
    for c in rng.sample(range(1, w), n_1):
        g[0][c] = 1
    for r in rng.sample(range(1, h), n_2):
        g[r][0] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_top_marks":
        # only left-column 2-marks → no column selectors, intersection set empty
        g[2][0] = 2; g[5][0] = 2
        return g
    if name == "no_left_marks":
        # only top-row 1-marks → no row selectors, intersection set empty
        g[0][3] = 1; g[0][6] = 1
        return g
    if name == "all_rows_all_cols":
        # every non-(0,0) row and col is marked → output is fully painted (saturated)
        for c in range(1, w): g[0][c] = 1
        for r in range(1, h): g[r][0] = 2
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """(0,0)=0; row 0 has >=1 one-mark at cols>=1; col 0 has >=1 two-mark at rows>=1."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    if grid[0][0] != 0:
        errors.append(f"(0,0) should be 0, found {grid[0][0]}")
    top_ones = [c for c in range(1, w) if grid[0][c] == 1]
    if not top_ones:
        errors.append("no 1-marks in row 0 at cols >= 1")
    left_twos = [r for r in range(1, h) if grid[r][0] == 2]
    if not left_twos:
        errors.append("no 2-marks in col 0 at rows >= 1")
    return errors
