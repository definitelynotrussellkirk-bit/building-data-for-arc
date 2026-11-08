"""Generator for arc_additional_puzzle_bank_volume23:H156 — wall-aware Voronoi 3-seed remap.

Rule: three seed colors compete by wall-aware distance, then map owners
and ties to output colors.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_seed, no_walls, all_seeds_in_one_chamber.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d7b74143cb92"
VERSION = "2.0.0"
TASK_ID = "d7b74143cb92"
SUMMARY = (
    "0-bg grid (h~9-13, w~12-17) with "
    "COLOR-5 (gray) WALLS: (a) FULL-"
    "HEIGHT VERTICAL WALL at col "
    "w//2 with a GAP at random row "
    "(in 3..h-4); (b) SHORT "
    "HORIZONTAL WALLS at row h//2 "
    "scattered on both sides at "
    "random columns (random "
    "True/False); This creates 2 "
    "CHAMBERS. THREE SEEDS placed at "
    "fixed corners: COLOR-4 at "
    "(1, wall_col-2), COLOR-3 at "
    "(h-2, 2), COLOR-2 at "
    "(h-2, w-3). Rule (WALL-AWARE "
    "VORONOI + TIE MAP): for EACH "
    "0-CELL, compute the SHORTEST "
    "BFS DISTANCE to each of the 3 "
    "SEEDS through walkable (non-5) "
    "cells. If one seed is strictly "
    "closest, MAP its color to "
    "{2 → 6, 3 → 7, 4 → 8}. If "
    "MULTIPLE seeds tie for "
    "closest, MAP to COLOR 9. "
    "Unreachable cells (separated "
    "by walls) get COLOR 9 or 0. "
    "Net: 3-seed wall-aware "
    "Voronoi, ties = 9."
)

INVARIANTS = [
    "background is 0",
    "gray cells are walls",
    "one seed of each color 2, 3, and 4 is present",
    "nearest-to-seed cells are remapped to 6, 7, and 8 while ties become 9",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_seed", "no_walls", "all_seeds_in_one_chamber")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "9..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "3", "valid": "3..3"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "wall_chambers_with_3_seeds",
                       "valid": "wall_chambers_with_3_seeds"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
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
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 16, 17)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 12, 17)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    wall_col = w // 2
    gap = rng.randint(3, h - 4)
    for r in range(1, h - 1):
        if r != gap:
            g[r][wall_col] = 5
    for c in range(1, wall_col):
        if c not in {2, wall_col - 1} and rng.choice([True, False]):
            g[h // 2][c] = 5
    for c in range(wall_col + 1, w - 1):
        if c not in {wall_col + 1, w - 3} and rng.choice([True, False]):
            g[h // 2][c] = 5
    g[1][wall_col - 2] = 4
    g[h - 2][2] = 3
    g[h - 2][w - 3] = 2
    return g




def self_check(grid, *, difficulty=None, meta=None):
    h, w = len(grid), len(grid[0])
    wall_col = w // 2
    errors = []
    for color in (2, 3, 4):
        n = sum(v == color for row in grid for v in row)
        if n != 1:
            errors.append(f"expected exactly one seed color {color}, got {n}")
    gaps = [r for r in range(1, h - 1) if grid[r][wall_col] != 5]
    if len(gaps) != 1:
        errors.append(f"expected one gap in the vertical wall, got {gaps}")
    if not any(grid[r][wall_col] == 5 for r in range(1, h - 1)):
        errors.append("vertical wall is missing")
    return errors

def _draw_from_degenerate(name, rng):
    h, w = 11, 14
    g = full_grid(h, w, 0)
    wall_col = w // 2
    gap = h // 2
    if name == "missing_seed":
        # only 2 of 3 seed colors → invariant says all 3 must be present
        for r in range(1, h - 1):
            if r != gap: g[r][wall_col] = 5
        g[1][wall_col - 2] = 4
        g[h - 2][2] = 3
        # color 2 missing
        return g
    if name == "no_walls":
        # walls absent → grid is one chamber, no wall-aware distance distinction
        g2 = full_grid(h, w, 0)
        g2[1][3] = 4; g2[h - 2][2] = 3; g2[h - 2][w - 3] = 2
        return g2
    if name == "all_seeds_in_one_chamber":
        # all 3 seeds in same chamber → one chamber empty (no Voronoi battle there)
        for r in range(1, h - 1):
            if r != gap: g[r][wall_col] = 5
        g[1][2] = 4
        g[3][2] = 3
        g[5][2] = 2
        return g
    return g
