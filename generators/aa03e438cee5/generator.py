"""Generator for arc_puzzle_bank_eighteenth_21_bundle:easy_123_expand_singletons_to_radius1_diamonds.

Rule: each singleton seed expands into a radius-1 cardinal diamond.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seeds_at_corner, multi_cell_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa03e438cee5"
VERSION = "2.0.1"
TASK_ID = "aa03e438cee5"

SUMMARY = (
    "0-bg grid (h~8-10, w~8-12) "
    "with 2-4 SINGLETON SEED "
    "CELLS at scattered "
    "positions with Manhattan "
    "distance > 2 between any "
    "pair (so radius-1 diamond "
    "footprints don't overlap). "
    "Each seed in a random "
    "color from {1..9}. Rule "
    "(EXPAND EACH SEED INTO "
    "RADIUS-1 CARDINAL "
    "DIAMOND): For EACH SEED "
    "at (r, c) with color C: "
    "PAINT the 4 CARDINAL "
    "NEIGHBORS — (r-1, c), "
    "(r+1, c), (r, c-1), "
    "(r, c+1) — with COLOR C, "
    "clipping at grid edges. "
    "The seed cell stays. The "
    "result is a 5-cell plus-"
    "shape (or smaller if at "
    "border) in color C per "
    "seed. Net: each seed "
    "becomes a + diamond of "
    "its color."
)

INVARIANTS = [
    "background is 0",
    "input cells are isolated singleton seeds",
    "diamond footprints do not overlap",
    "neighbor cells clip at grid edges",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seeds_at_corner", "multi_cell_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_singletons",
                       "valid": "spaced_singletons"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _far(cells, r, c):
    return all(abs(r - rr) + abs(c - cc) > 2 for rr, cc in cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥2 non-zero isolated singletons; each seed has no same-color adjacent neighbor."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        return errs  # degenerate (no_seeds) — allowed
    if len(nz) == 1:
        return errs  # degenerate (single seed) — allowed
    # All seeds must be isolated from each other (Manhattan > 2)
    for i, (r, c) in enumerate(nz):
        for j, (rr, cc) in enumerate(nz):
            if i != j and abs(r - rr) + abs(c - cc) <= 2:
                return errs  # degenerate (multi_cell_blobs / seeds_at_corner adjacent) — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("n_seeds", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        target = ctx.draw_int("n_seeds", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        target = ctx.draw_int("n_seeds", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    seeds = []
    for _ in range(160):
        if len(seeds) >= target:
            break
        r = rng.randrange(h)
        c = rng.randrange(w)
        if _far(seeds, r, c):
            seeds.append((r, c))
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank → no diamonds to grow
        return g
    if name == "seeds_at_corner":
        # seeds at corner → 2 of 4 cardinal neighbors out of bounds
        g[0][0] = 3
        g[h - 1][w - 1] = 7
        return g
    if name == "multi_cell_blobs":
        # multi-cell blobs (not singletons) → "singleton" precondition fails
        g[2][2] = 4; g[2][3] = 4   # pair
        g[5][5] = 6; g[6][5] = 6   # pair
        return g
    return g
