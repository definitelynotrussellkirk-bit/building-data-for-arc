"""Generator for arc_additional_puzzles_21_set12_bundle:H80 — Voronoi inside 9-frame, ties → 8.

Rule: 9-frame surrounds interior with seeds. For each empty cell, find
nearest seeds (Manhattan); if unique color → that color, else → 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, single_seed, broken_frame.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7a282fc6a35e"
VERSION = "1.1.0"
TASK_ID = "7a282fc6a35e"
SUMMARY = "9-frame around interior + 2-3 distinct-color seeds inside."

INVARIANTS = [
    "9-frame on outer border",
    "interior has 2-3 single-cell seeds of distinct non-{0,9} colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "single_seed", "broken_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "9frame_with_voronoi_seeds",
                       "valid": "9frame_with_voronoi_seeds"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 11, 13)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    for c in range(w):
        g[0][c] = 9; g[h - 1][c] = 9
    for r in range(h):
        g[r][0] = 9; g[r][w - 1] = 9
    palette = [2, 3, 4, 5, 6, 7]; rng.shuffle(palette)
    n = rng.randint(2, 3)
    placed = 0
    while placed < n:
        sr = rng.randint(2, h - 3)
        sc = rng.randint(2, w - 3)
        if g[sr][sc] == 0:
            g[sr][sc] = palette[placed]; placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 9; g[h - 1][c] = 9
    for r in range(h): g[r][0] = 9; g[r][w - 1] = 9
    if name == "no_seeds":
        # frame but no seeds → no Voronoi sources, interior empty
        return g
    if name == "single_seed":
        # only 1 seed → entire interior becomes that color (no tie-cells, no 8)
        g[4][5] = 4
        return g
    if name == "broken_frame":
        # frame has gap → "interior" leaks to outside, Voronoi escapes
        g[0][5] = 0   # gap in top edge
        g[3][3] = 4
        g[5][8] = 6
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if not all(grid[0][c] == 9 and grid[h - 1][c] == 9 for c in range(w)):
        errors.append("top/bottom frame rows must be color 9")
    if not all(grid[r][0] == 9 and grid[r][w - 1] == 9 for r in range(h)):
        errors.append("left/right frame columns must be color 9")
    seeds = [(r, c, grid[r][c]) for r in range(1, h - 1) for c in range(1, w - 1)
             if grid[r][c] not in (0, 9)]
    if not (2 <= len(seeds) <= 3):
        errors.append(f"expected 2..3 interior seeds, found {len(seeds)}")
    colors = [v for _, _, v in seeds]
    if len(colors) != len(set(colors)):
        errors.append("seed colors must be distinct")
    return errors

