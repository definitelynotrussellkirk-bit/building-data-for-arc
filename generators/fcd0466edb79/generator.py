"""Generator for arc_puzzle_bank_eleventh21:M77 — select cols by row-0 1-marks.

Rule: row 0 has 1-markers at certain cols. Output is the rows below
row 0, restricted to only the marked cols.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_marks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marks, all_cols_marked, body_empty.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fcd0466edb79"
VERSION = "2.0.0"  # more marks (wider output) + wider/taller grids + varied body density/colors
TASK_ID = "fcd0466edb79"
SUMMARY = (
    "0-bg grid: row 0 has 2-8 color-1 MARKERS at distinct "
    "columns (at least one column unmarked); rows below row "
    "0 hold dense colored content (colors 1-9). Rule: take "
    "the columns marked with a 1 in row 0; output the rows "
    "below row 0 restricted to exactly those columns (a "
    "(h-1) x n_marks sub-grid). Net: the marked columns of "
    "the body are extracted in order."
)

INVARIANTS = [
    "row 0 has 2-8 color-1 cells at distinct columns, with >=1 column unmarked",
    "rows below row 0 contain non-zero content in the marked columns (output non-trivial)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marks", "all_cols_marked", "body_empty")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "5-7 easy / 6-10 med / 8-14 hard", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "7-9 easy / 9-13 med / 12-18 hard", "valid": "6..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_marks":        {"type": "int", "default": "2-3 easy / 2-5 med / 3-8 hard", "valid": "1..9"},
    "body_density":   {"type": "float", "default": "rng 0.4..0.7", "valid": "0..1"},
    "palette_size":   {"type": "int", "default": "rng colors 1..9", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "row0_marker",
                       "valid": "row0_marker"},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "2..9"},
    "density":        {"type": "str", "default": "medium", "valid": "medium"},
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
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 9)
        nm_lo, nm_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 12, 18)
        nm_lo, nm_hi = 3, 8
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 9, 13)
        nm_lo, nm_hi = 2, 5
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    n_cols = rng.randint(nm_lo, min(nm_hi, w - 1))   # >=1 column stays unmarked
    cols = rng.sample(range(w), n_cols)
    for c in cols:
        g[0][c] = 1
    density = rng.uniform(0.4, 0.7)
    body_palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for r in range(1, h):
        for c in range(w):
            if rng.random() < density:
                g[r][c] = rng.choice(body_palette)
    # Guarantee >=1 non-zero in the marked columns below row 0 (non-trivial output).
    if not any(g[r][c] for r in range(1, h) for c in cols):
        g[1][cols[0]] = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    palette = [2, 3, 4, 5, 6, 7, 8, 9]
    if name == "no_marks":
        # row 0 has no 1-markers → no columns selected, output has 0 columns (ambiguous)
        for r in range(1, h):
            for c in range(w):
                if (r * 3 + c) % 3 == 0:
                    g[r][c] = palette[(r + c) % len(palette)]
        return g
    if name == "all_cols_marked":
        # every column marked → output equals body without row 0, rule effect minimal
        for c in range(w):
            g[0][c] = 1
        for r in range(1, h):
            for c in range(w):
                if (r + c) % 2 == 0:
                    g[r][c] = palette[(r + c) % len(palette)]
        return g
    if name == "body_empty":
        # marks present but body all zeros → output is all-zero strip, no information
        for c in [1, 4, 6]:
            g[0][c] = 1
        return g
    return g
