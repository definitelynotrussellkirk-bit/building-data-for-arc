"""Generator for arc_additional_puzzle_bank_volume19:M129 — Intersection of red rows and green cols.

Rule:
  - rs = unique row coords of red(2) cells
  - cs = unique col coords of green(3) cells
  - Output: blank grid with (r, c) painted 8 for every (r, c) in rs x cs.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_red,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_red, no_green, marker_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "287285d0145f"
VERSION = "2.0.0"
TASK_ID = "287285d0145f"
SUMMARY = (
    "0-bg grid (h~6-10, w~6-10) with: "
    "(a) SCATTERED RED (COLOR 2) CELLS — "
    "2-6 cells placed on a small set of "
    "DISTINCT ROWS (1-4 rows total): each "
    "red cell at a random column on one of "
    "the selected red_rows; (b) SCATTERED "
    "GREEN (COLOR 3) CELLS — 2-6 cells "
    "placed on a small set of DISTINCT "
    "COLS (1-4 cols total): each green "
    "cell at a random row on one of the "
    "selected green_cols. Red and green "
    "cells don't share positions. "
    "Rule (INTERSECTION OF RED ROWS WITH "
    "GREEN COLS, PAINTED WITH COLOR 8): "
    "compute rs = SET OF DISTINCT ROW "
    "INDICES of all RED CELLS in the "
    "input. compute cs = SET OF DISTINCT "
    "COLUMN INDICES of all GREEN CELLS. "
    "PRODUCE a fresh same-size grid of "
    "0s; for EVERY (r, c) WHERE r ∈ rs "
    "AND c ∈ cs: PAINT output[r][c] = "
    "COLOR 8 (cyan). Net: red markers "
    "broadcast horizontally, green "
    "markers broadcast vertically; "
    "their grid intersection becomes a "
    "cyan dot pattern on a blank "
    "canvas."
)

INVARIANTS = [
    "between 1 and 4 distinct red rows",
    "between 1 and 4 distinct green cols",
    "red and green cells don't overlap (impossible since they're at distinct (r, c))",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_red", "no_green", "marker_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_red":          {"type": "int", "default": "rng 2..6", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "row_col_scatter",
                       "valid": "row_col_scatter"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "n_green":        {"type": "int", "default": "rng 2..6", "valid": "1..10"},
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
        w = ctx.draw_int("grid_w", 6, 7)
        n_red = ctx.draw_int("n_red", 2, 3)
        n_green = ctx.draw_int("n_green", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n_red = ctx.draw_int("n_red", 4, 6)
        n_green = ctx.draw_int("n_green", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 6, 10)
        n_red = ctx.draw_int("n_red", 2, 6)
        n_green = ctx.draw_int("n_green", 2, 6)

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("placement")

    rows = list(range(h)); rng.shuffle(rows)
    red_rows = rows[:min(4, max(1, n_red // 2 + 1))]
    used = set()
    placed_red = 0
    while placed_red < n_red:
        r = rng.choice(red_rows)
        c = rng.randint(0, w - 1)
        if (r, c) in used: continue
        g[r][c] = 2
        used.add((r, c))
        placed_red += 1

    cols = list(range(w)); rng.shuffle(cols)
    green_cols = cols[:min(4, max(1, n_green // 2 + 1))]
    placed_green = 0
    while placed_green < n_green:
        c = rng.choice(green_cols)
        r = rng.randint(0, h - 1)
        if (r, c) in used or g[r][c] != 0: continue
        g[r][c] = 3
        used.add((r, c))
        placed_green += 1

    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_red":
        # no red cells → rs is empty, intersection is empty, output is all-zero
        for r, c in [(2, 3), (4, 5), (6, 7)]:
            g[r][c] = 3
        return g
    if name == "no_green":
        # no green cells → cs is empty, output is all-zero
        for r, c in [(1, 2), (4, 5), (7, 1)]:
            g[r][c] = 2
        return g
    if name == "marker_overlap":
        # row of a red and col of a green coincide at one cell, with mixed coloring at boundaries
        for r, c in [(2, 1), (2, 5)]:
            g[r][c] = 2
        for r, c in [(0, 5), (5, 5)]:
            g[r][c] = 3
        # the intersection (2, 5) was already red, then green can't sit there — ambiguous source
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    reds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    greens = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    red_rows = {r for r, _ in reds}
    green_cols = {c for _, c in greens}
    if not reds or not greens:
        errs.append("normal examples need both red row markers and green column markers")
    if not (1 <= len(red_rows) <= 4):
        errs.append("expected 1..4 distinct red rows")
    if not (1 <= len(green_cols) <= 4):
        errs.append("expected 1..4 distinct green columns")
    if any(v not in (0, 2, 3) for row in grid for v in row):
        errs.append("normal examples should only use colors 0,2,3")
    return errs
