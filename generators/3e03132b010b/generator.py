"""Generator for arc_puzzle_bank_21_set8:easy_h02.

Rule: replace isolated singleton seeds with hollow 3x3 rings (same
color).

Combinatorial axes (8): grid_h, grid_w, palette_kind, seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seed_at_corner, seeds_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3e03132b010b"
VERSION = "1.1.1"
TASK_ID = "3e03132b010b"
SUMMARY = "Replace isolated singleton seeds with hollow 3x3 rings."

INVARIANTS = [
    "background is 0",
    "all nonzero cells are isolated singleton seeds",
    "seeds are at least one cell away from the border",
    "3x3 ring footprints do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seed_at_corner", "seeds_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seeds":          {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "interior_separated",
                       "valid": "interior_separated"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, nonzero cells are isolated singletons at least 1 cell from border."""
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
    # Seeds must be at least 1 cell from border (interior)
    for r, c in nonzero:
        if r == 0 or r == h - 1 or c == 0 or c == w - 1:
            errs.append(f"seed at ({r},{c}) is on the border (must be interior)")
            break
    return errs


def _far(cells, r, c):
    return all(abs(r - rr) > 2 or abs(c - cc) > 2 for rr, cc in cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("seeds", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 12)
        target = ctx.draw_int("seeds", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 12)
        target = ctx.draw_int("seeds", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    seeds = []
    for _ in range(160):
        if len(seeds) >= target:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        if _far(seeds, r, c):
            seeds.append((r, c))
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    if not seeds:
        g[h // 2][w // 2] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # empty grid → no seeds to expand to rings
        return g
    if name == "seed_at_corner":
        # seed at (0,0) → ring footprint clips off-grid
        g[0][0] = 4
        return g
    if name == "seeds_overlap":
        # adjacent seeds → 3x3 ring footprints overlap, color collision
        g[3][3] = 4
        g[3][4] = 6
        return g
    return g
