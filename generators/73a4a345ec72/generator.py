"""Generator for arc_additional_puzzles_21_set16_bundle:H107.

Rule: 5-frame surrounds interior with seeds. For each empty cell, find
nearest seeds; if unique color → that color, ties → 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_seeds, single_seed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "73a4a345ec72"
VERSION = "1.1.1"
TASK_ID = "73a4a345ec72"
SUMMARY = "5-frame around interior + 2-3 distinct-color seeds."

INVARIANTS = [
    "5-frame on outer border",
    "interior has 2-3 single-cell seeds of distinct non-{0,5} colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_seeds", "single_seed")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "interior_seeds",
                       "valid": "interior_seeds"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "density":        {"type": "str", "default": "framed", "valid": "framed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: outer border is all color-5, interior has non-{0,5} seed cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    # Check outer border is all 5
    border_cells = ([grid[0][c] for c in range(w)] + [grid[h-1][c] for c in range(w)] +
                    [grid[r][0] for r in range(1, h-1)] + [grid[r][w-1] for r in range(1, h-1)])
    if any(v != 5 for v in border_cells):
        errs.append("outer border is not all color-5")
    # Check interior has seed cells (non-{0,5})
    seeds = [(r, c) for r in range(1, h-1) for c in range(1, w-1) if grid[r][c] not in (0, 5)]
    if not seeds:
        errs.append("no interior seed cells (non-{0,5}) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 9, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    for c in range(w):
        g[0][c] = 5; g[h - 1][c] = 5
    for r in range(h):
        g[r][0] = 5; g[r][w - 1] = 5
    palette = [2, 3, 4, 6, 7]; rng.shuffle(palette)
    n = rng.randint(2, 3)
    placed = 0
    while placed < n:
        sr = rng.randint(2, h - 3); sc = rng.randint(2, w - 3)
        if g[sr][sc] == 0:
            g[sr][sc] = palette[placed]; placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # seeds without frame → voronoi extends to grid edges
        g[3][3] = 4; g[5][7] = 6
        return g
    if name == "no_seeds":
        # frame but no seeds → no sources for distance computation
        for c in range(w): g[0][c] = 5; g[h - 1][c] = 5
        for r in range(h): g[r][0] = 5; g[r][w - 1] = 5
        return g
    if name == "single_seed":
        # one seed → entire interior takes its color, no ties possible
        for c in range(w): g[0][c] = 5; g[h - 1][c] = 5
        for r in range(h): g[r][0] = 5; g[r][w - 1] = 5
        g[3][5] = 4
        return g
    return g
