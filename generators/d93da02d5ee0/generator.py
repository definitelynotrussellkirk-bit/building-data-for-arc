"""Generator for arc_puzzle_bank_21_set12_bundle:easy_l07 — X → + transform.

Rule: find each X-shape (5 cells: center + 4 diagonal corners). Replace
with + shape: center + 4 cardinal neighbors.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_x,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_X_shapes, partial_X, X_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d93da02d5ee0"
VERSION = "1.1.0"
TASK_ID = "d93da02d5ee0"
SUMMARY = "2-3 X-shapes (center + 4 diagonal corners) of distinct colors, well separated."

INVARIANTS = [
    "2-3 X-shapes (3×3 footprint each)",
    "centers are ≥4 cells apart",
    "centers at interior positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_X_shapes", "partial_X", "X_at_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_x":            {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "spaced_X_shapes",
                       "valid": "spaced_X_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    n_x = rng.randint(2, 3)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_x)
    centers = []
    for color in palette:
        for _ in range(40):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if any(abs(r - pr) + abs(c - pc) < 4 for pr, pc in centers):
                continue
            for dr, dc in [(0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                g[r + dr][c + dc] = color
            centers.append((r, c))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_X_shapes":
        # blank → no X to replace
        return g
    if name == "partial_X":
        # some diagonal corners missing → "5 cells X" precondition fails
        g[3][3] = 4
        g[2][2] = 4; g[2][4] = 4   # missing the bottom diagonals
        g[5][5] = 6
        g[4][4] = 6; g[6][6] = 6   # only one diagonal pair
        return g
    if name == "X_at_corner":
        # X centered at (1,1) → diagonal arm at (0,0) ok but (2,2) etc within bounds;
        # use a true edge case: center at edge so 1+ diagonal arms are out of bounds
        g[0][0] = 4
        g[1][1] = 4   # only one diagonal cell exists
        return g
    return g
