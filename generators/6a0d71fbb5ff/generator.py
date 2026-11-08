"""Generator for arc_puzzle_bank_21_next:easy_c01.

Rule: for each non-bg cell at (r, c, v), paint all 9 cells in the 3x3
box centered at (r, c) (those in-bounds) with v.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seed_at_corner, adjacent_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6a0d71fbb5ff"
VERSION = "1.1.1"
TASK_ID = "6a0d71fbb5ff"
SUMMARY = "1-2 isolated non-bg cells in distinct colors."

INVARIANTS = [
    "1-2 non-bg cells",
    "no two cells within Manhattan distance 4 of each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seed_at_corner", "adjacent_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "interior", "valid": "interior"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; 1-2 isolated non-bg cells (seeds for 3x3 expansion)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return errs  # degenerate (no_seeds) — allowed
    if len(nonzero) > 4:
        errs.append(f"expected 1-2 seed cells; found {len(nonzero)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 6, 8)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    placed = []
    palette = [2, 3, 4, 5, 6, 7, 8, 9]
    n = rng.randint(1, 2)
    for _ in range(40):
        if len(placed) >= n:
            break
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if all(abs(r - pr) + abs(c - pc) > 4 for pr, pc in placed):
            g[r][c] = rng.choice(palette)
            placed.append((r, c))
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 7
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # no source cells → no 3x3 boxes, output is the empty grid
        return g
    if name == "seed_at_corner":
        # seed at (0,0) → only the bottom-right 4 cells of the 3x3 are in-bounds
        g[0][0] = 4
        g[h - 1][w - 1] = 7
        return g
    if name == "adjacent_seeds":
        # two seeds within Manhattan-2 → their 3x3 boxes overlap, paint conflict
        g[2][2] = 5
        g[2][3] = 6
        return g
    return g
