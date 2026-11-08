"""Generator for arc_puzzle_bank_21_set6_s:S6_E4.

Rule: three same-color rectangle corners imply the missing fourth corner.

Combinatorial axes (8): grid_h, grid_w, palette_kind, missing_corner,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: only_2_corners, all_4_corners, collinear_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "da16c00eed25"
VERSION = "2.0.0"
TASK_ID = "da16c00eed25"
SUMMARY = (
    "0-bg grid (h~6-9, w~"
    "7-11) with EXACTLY 3 "
    "SAME-COLOR CELLS at "
    "positions forming "
    "THREE OF FOUR CORNERS "
    "of an axis-aligned "
    "rectangle: rows ∈ "
    "{r1, r2} (r2 - r1 ≥ "
    "2), cols ∈ {c1, c2} "
    "(c2 - c1 ≥ 2). The "
    "MISSING CORNER (one "
    "of 4 positions, "
    "randomly chosen) is "
    "BLANK. The 3 cells "
    "share a SINGLE NON-0 "
    "COLOR. Rule (INFER "
    "THE MISSING 4TH "
    "CORNER FROM THE 3 "
    "GIVEN): find the 3 "
    "same-color cells. "
    "They occupy 2 "
    "distinct rows and 2 "
    "distinct columns. "
    "The MISSING corner "
    "is at the (row, col) "
    "combination NOT "
    "currently occupied "
    "(the unique (r, c) "
    "where r ∈ {r1, r2}, "
    "c ∈ {c1, c2}, and "
    "(r, c) is not in "
    "input). PAINT the "
    "missing corner with "
    "the shared color. "
    "Other cells stay. "
    "Net: 3 corners "
    "complete to all 4 "
    "corners of the "
    "implied rectangle."
)

INVARIANTS = [
    "background is 0",
    "exactly three same-color nonzero cells are present",
    "the cells occupy two distinct rows and two distinct columns",
    "the missing row-column combination is blank",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("only_2_corners", "all_4_corners", "collinear_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "missing_corner": {"type": "choice", "default": "rng 0..3", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "rect_corners",
                       "valid": "rect_corners"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 11)
    missing = ctx.draw_choice("missing_corner", list(range(4)))
    rng = ctx.draw_rng("layout")
    color = ctx.draw_color("corner_color", exclude={0})
    g = full_grid(h, w, 0)
    r1 = rng.randint(1, h - 3)
    r2 = rng.randint(r1 + 2, h - 1)
    c1 = rng.randint(1, w - 4)
    c2 = rng.randint(c1 + 2, w - 1)
    corners = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
    for idx, (r, c) in enumerate(corners):
        if idx != missing:
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "only_2_corners":
        # only 2 corners → cannot determine the missing one (multiple possibilities)
        g[1][1] = 4
        g[5][6] = 4
        return g
    if name == "all_4_corners":
        # 4 corners already set → nothing missing, rule is identity
        for r, c in [(1, 1), (1, 6), (5, 1), (5, 6)]: g[r][c] = 4
        return g
    if name == "collinear_corners":
        # 3 cells on the same row → no rectangle defined
        g[3][1] = 4
        g[3][4] = 4
        g[3][7] = 4
        return g
    return g
