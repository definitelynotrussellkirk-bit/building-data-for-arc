"""Generator for arc_additional_puzzles_21_set9:E60 — Draw rect outline from 4 corner cells.

Rule: for each color appearing as 4 cells forming a rectangle's
corners, draw the full outline.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_corners, partial_corners, collinear_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f65705efd235"
VERSION = "2.0.0"  # more colors + full-size + OVERLAPPING rectangles (was <=2, <=6x6, non-overlapping)
TASK_ID = "f65705efd235"
SUMMARY = (
    "0-bg grid (size varies, up to ~24). Several distinct colors, each placed as "
    "exactly the 4 CORNERS of a rectangle (bbox >=3x3, sizes span the grid). The "
    "rectangles' spans may OVERLAP (only the corner cells are kept distinct). "
    "Rule: for each color appearing as 4 rectangle corners, draw that rectangle's "
    "outline in its color. Net: each corner quad blooms into a rectangle outline; "
    "overlapping outlines layer by color order. (Was: 1-2 colors, <=6x6, "
    "non-overlapping.)"
)

INVARIANTS = [
    ">=1 distinct non-bg color, each placed as exactly 4 rectangle corners",
    "each color's bbox is >=3x3 (a real rectangle, not a line)",
    "all corner cells are on distinct cells (rectangles may otherwise overlap)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_corners", "partial_corners", "collinear_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-10 easy / 10-16 med / 14-24 hard", "valid": "5..26"},
    "grid_w":         {"type": "int", "default": "8-11 easy / 10-16 med / 14-24 hard", "valid": "6..26"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rects":        {"type": "int", "default": "1-2 easy / 2-4 med / 3-6 hard", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 1..2", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "4_corner_pairs_per_color",
                       "valid": "4_corner_pairs_per_color"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..2", "valid": "1..8"},
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
        hr, wr, nr = (7, 10), (8, 11), (1, 2)
    elif difficulty == "hard":
        hr, wr, nr = (14, 24), (14, 24), (3, 6)
    else:
        hr, wr, nr = (10, 16), (10, 16), (2, 4)
    rng = ctx.draw_rng("layout")
    h = rng.randint(*hr); w = rng.randint(*wr)
    g = full_grid(h, w, 0)
    n_rects = min(rng.randint(*nr), 8)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_rects)
    used = set()                                  # corner cells; rects may overlap, corners may not
    placed = 0
    for color in palette:
        for _ in range(50):
            r1 = rng.randint(0, h - 3); r2 = rng.randint(r1 + 2, h - 1)
            c1 = rng.randint(0, w - 3); c2 = rng.randint(c1 + 2, w - 1)
            corners = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
            if any(p in used for p in corners):
                continue
            for p in corners:
                g[p[0]][p[1]] = color; used.add(p)
            placed += 1
            break
    if placed == 0:                              # deterministic fallback
        for r, c in [(1, 1), (1, 5), (5, 1), (5, 5)]:
            g[r][c] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_corners":
        # blank → no corners to interpret as rectangles
        return g
    if name == "partial_corners":
        # only 2 or 3 corners per color → can't define a rectangle
        g[1][1] = 4; g[1][6] = 4; g[5][1] = 4
        return g
    if name == "collinear_corners":
        # 4 cells but all in same row/col → degenerate to a line, not a rect
        g[3][1] = 4; g[3][3] = 4; g[3][6] = 4; g[3][8] = 4
        return g
    return g
