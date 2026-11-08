"""Generator for arc_puzzle_bank_21_set18_bundle:easy_p03 — diamond shell at distance 2.

Rule: each seed paints the Manhattan-distance-two diamond shell around
itself.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, multi_cell_blobs, seeds_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d349f4dfe492"
VERSION = "1.1.1"
TASK_ID = "d349f4dfe492"
SUMMARY = "Separated singleton seeds for distance-two diamond growth."

INVARIANTS = [
    "background is 0",
    "all nonzero cells are singleton seeds",
    "distance-two diamond neighborhoods do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "multi_cell_blobs", "seeds_at_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "5..15"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_singletons",
                       "valid": "spaced_singletons"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _diamond_zone(r, c):
    return {(rr, cc) for rr in range(r - 2, r + 3) for cc in range(c - 2, c + 3)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 non-zero seed cell; all seed colors appear exactly once (singletons)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    h, w = len(grid), len(grid[0])
    counts = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        errs.append("no non-zero seed cells found")
        return errs
    # all seed colors should appear exactly once (singletons)
    multi = [k for k, v in counts.items() if v > 1]
    if multi:
        errs.append(f"seed colors with >1 cell (not singleton): {multi}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        seed_count = ctx.draw_int("n_seeds", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 11, 12)
        seed_count = ctx.draw_int("n_seeds", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        seed_count = ctx.draw_int("n_seeds", 2, 3)
    colors = ctx.draw_distinct_colors("colors", n=seed_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    occupied = set()
    for color in colors:
        for _ in range(300):
            r = rng.randrange(h)
            c = rng.randrange(w)
            zone = _diamond_zone(r, c)
            if not (zone & occupied):
                g[r][c] = color
                occupied |= zone
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank → no diamond shells to grow
        return g
    if name == "multi_cell_blobs":
        # multi-cell blobs (not singletons) → "singleton" precondition fails
        g[2][2] = 4; g[2][3] = 4
        g[5][5] = 6; g[6][5] = 6
        return g
    if name == "seeds_at_corner":
        # seeds at corners → most of the diamond shell out of bounds
        g[0][0] = 3
        g[h - 1][w - 1] = 7
        return g
    return g
