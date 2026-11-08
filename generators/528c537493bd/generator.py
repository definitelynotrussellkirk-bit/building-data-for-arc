"""Generator for v3_rich_schema:medium_07_raycast_cross_from_centers — rays in 4 directions from each center.

Rule: each emitter cell shoots rays in 4 cardinal directions, painting bg
cells along the way (stops at any non-bg, including other emitters).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_emitters,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_emitters, emitters_at_corners_only, already_painted.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "528c537493bd"
VERSION = "2.0.1"
TASK_ID = "528c537493bd"
SUMMARY = "1-3 emitter cells; rest of the grid is empty."

INVARIANTS = [
    "background is 0",
    "1-3 emitter cells at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_emitters", "emitters_at_corners_only", "already_painted")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_emitters":     {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; at least one non-bg emitter cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    non_bg = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not non_bg:
        errors.append("no non-background (emitter) cells found")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
        n = ctx.draw_int("n_emitters", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        n = ctx.draw_int("n_emitters", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 11)
        n = ctx.draw_int("n_emitters", 1, 3)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    for _ in range(n):
        for _t in range(80):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0: continue
            g[r][c] = 6
            break
    # color-5 WALLS that stop the rays (the rule's stop-branch; canonical has
    # color-5 walls — the old gen omitted them so rays always reached the edge
    # and the branch was never exercised, palette-locked to 2 colours).
    n_walls = rng.randint(max(1, (h * w) // 18), max(2, (h * w) // 9))
    for _ in range(n_walls):
        for _t in range(40):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if g[r][c] != 0:
                continue
            g[r][c] = 5
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_emitters":
        # empty grid → no rays to cast
        return g
    if name == "emitters_at_corners_only":
        # all emitters at corners → only 2 rays per emitter (others go off-grid trivially)
        g[0][0] = 6
        g[h - 1][w - 1] = 6
        return g
    if name == "already_painted":
        # cells along ray paths are already non-bg → rays stop at first cell, no fill
        g[3][3] = 6
        g[3][2] = 4; g[3][4] = 5
        g[2][3] = 7; g[4][3] = 8
        return g
    return g
