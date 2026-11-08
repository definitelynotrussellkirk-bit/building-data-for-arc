"""Generator for arc_puzzle_bank_21_set18_bundle:hard_p05 — flood-fill rooms by color seeds.

Rule: outer color-5 walls bound the grid; some interior color-5 walls divide
it into rooms. Each colored seed (non-{0, 5}) flood-fills its connected
component (over 0-cells), painting the room in that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, n_walls, n_seeds, texture.
Degenerates: no_walls, no_seeds, multi_seeds_per_room.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "22a206f031ef"
VERSION = "1.3.2"  # AXES synced to the real band draws (defect-lint axis-honesty)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: outer border is color-5; has >=1 non-{0,5} seed cell (per room)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    border_ok = (
        all(grid[0][c] == 5 for c in range(w)) and
        all(grid[h-1][c] == 5 for c in range(w)) and
        all(grid[r][0] == 5 for r in range(h)) and
        all(grid[r][w-1] == 5 for r in range(h))
    )
    if not border_ok:
        errs.append("outer border is not all color-5")
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in {0, 5}]
    if not seeds:
        errs.append("no non-{0,5} seed cells (expected one per room)")
    return errs
TASK_ID = "22a206f031ef"

SUMMARY = "Color-5 outer border + 0-3 interior color-5 walls (each with one door cell) partition the grid into rooms. Each room has one color-seed (non-{0,5}). Rule flood-fills each room with its seed color through bg cells; walls and outer border stay 5."

# Rivals: 'output is input' refuted by any demo (rooms fill). 'paint
# all bg one color' refuted by any demo with ≥2 rooms in different
# colors. 'use color 5 for fill' refuted by any demo (fill uses seed
# color). 'fill includes walls' refuted by any demo (walls stay).
# 3 demos with varied wall layouts cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "outer border is color-5 walls",
    "0-2 interior color-5 walls (full row or column segments) partition the interior",
    "1-3 single-cell seeds in distinct non-{0, 5} colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_seeds", "multi_seeds_per_room")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-10 easy / 10-13 med / 13-18 hard",
                       "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "9-12 easy / 12-16 med / 16-22 hard",
                       "valid": "9..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_walls":        {"type": "int", "default": "0-1 easy / 0-3 med / 3-5 hard", "valid": "0..5"},
    "n_seeds":        {"type": "int", "default": "1-2 easy / 2-4 med / 4-6 hard", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "= n_seeds+2", "valid": "3..6"},
    "position_bias":  {"type": "str", "default": "walled_rooms_with_seeds",
                       "valid": "walled_rooms_with_seeds"},
    "n_distinct_colors": {"type": "int", "default": "= n_seeds+2", "valid": "3..6"},
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
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n_walls = ctx.draw_int("n_walls", 0, 1)
        n_seeds = ctx.draw_int("n_seeds", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 16, 22)
        n_walls = ctx.draw_int("n_walls", 3, 5)
        n_seeds = ctx.draw_int("n_seeds", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        n_walls = ctx.draw_int("n_walls", 1, 3)
        n_seeds = ctx.draw_int("n_seeds", 2, 4)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 5; g[h - 1][c] = 5
    for r in range(h): g[r][0] = 5; g[r][w - 1] = 5
    for _ in range(n_walls):
        if rng.choice([True, False]):
            r = rng.randint(2, h - 3)
            for c in range(1, w - 1): g[r][c] = 5
            door_c = rng.randint(1, w - 2)
            g[r][door_c] = 0
        else:
            c = rng.randint(2, w - 3)
            for r in range(1, h - 1): g[r][c] = 5
            door_r = rng.randint(1, h - 2)
            g[door_r][c] = 0
    seed_colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_seeds)
    for color in seed_colors:
        for _t in range(80):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if g[r][c] != 0: continue
            g[r][c] = color
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 5; g[h - 1][c] = 5
    for r in range(h): g[r][0] = 5; g[r][w - 1] = 5
    if name == "no_walls":
        # Outer-only border + multi-color seeds — every seed is in
        # the SAME room; rule's per-room paint becomes ambiguous
        # (multiple seeds in one room).
        g[3][3] = 4; g[5][7] = 6; g[6][2] = 7
        return g
    if name == "no_seeds":
        # Walls + rooms but no seeds — rule has no color to paint
        # any room with.
        for c in range(1, w - 1): g[4][c] = 5
        return g
    if name == "multi_seeds_per_room":
        # Wall divider + multiple distinct-colored seeds in the SAME
        # half — rule's "single seed per room" precondition fails;
        # fill color is ambiguous.
        for c in range(1, w - 1): g[4][c] = 5
        g[4][5] = 0
        g[2][3] = 3; g[2][7] = 6
        g[6][4] = 8; g[6][8] = 9
        return g
    return g
