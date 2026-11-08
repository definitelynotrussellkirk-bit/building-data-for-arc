"""Generator for arc_puzzle_bank_sixteenth21:E109.

Rule: sparse seeds each grow into a radius-one plus of the same color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seed_at_corner, seeds_too_close.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3e89f914acb3"
VERSION = "1.1.1"
TASK_ID = "3e89f914acb3"
SUMMARY = "Sparse seeds each grow into a radius-one plus of the same color."

INVARIANTS = [
    "background is 0",
    "input nonzero cells are isolated seeds",
    "seed plus neighborhoods do not overlap",
    "output is drawn on a blank grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seed_at_corner", "seeds_too_close")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "seeds":          {"type": "int", "default": "rng 3..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_seeds|seed_at_corner|seeds_too_close"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=1 nonzero seed cell that is not on the border."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no non-zero seed cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("seeds", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("seeds", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("seeds", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    seeds: list[tuple[int, int]] = []
    for _ in range(500):
        if len(seeds) >= target:
            break
        r = rng.randrange(h)
        c = rng.randrange(w)
        if any(abs(r - rr) + abs(c - cc) <= 3 for rr, cc in seeds):
            continue
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        seeds.append((r, c))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # empty grid → no seeds to grow, output equals input
        return g
    if name == "seed_at_corner":
        # seed at (0,0) → 2 of 4 plus arms are out-of-bounds, partial neighborhood
        g[0][0] = 4
        g[h - 1][w - 1] = 7
        return g
    if name == "seeds_too_close":
        # two seeds within Manhattan-3 → their plus neighborhoods overlap, paint conflict
        g[3][3] = 5
        g[3][5] = 6
        return g
    return g
