"""Generator for arc_additional_puzzle_bank_volume8:H55 — Voronoi via gray-wall corridors.

Rule: open cells take the strictly nearer red or green seed through
gray-wall corridors.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls, single_seed, no_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b18c5b4a8745"
VERSION = "2.0.1"
TASK_ID = "b18c5b4a8745"
SUMMARY = (
    "Grid (h~9-13, w~10-15) with: (a) color-5 (gray) WALLS "
    "forming a central vertical wall (with a gap) and "
    "horizontal cross-walls; (b) exactly ONE color-2 (red) "
    "seed on the left side and ONE color-3 (green) seed on "
    "the right side. Rule: do BFS-shortest-path distance "
    "from all red cells (d2) and from all green cells (d3), "
    "treating color-5 cells as impassable. For each cell: if "
    "input != 0 → keep it. Else compare d2 vs d3: if d2 < d3 "
    "→ paint 2; if d3 < d2 → paint 3; tie → 0. Net: "
    "wall-aware nearest-seed Voronoi between red and green."
)

INVARIANTS = [
    "background is 0",
    "gray walls partially block shortest paths",
    "there is exactly one red seed and one green seed",
    "some cells are nearer to each seed and ties remain 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "single_seed", "no_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..13", "valid": "7..24"},
    "grid_w":         {"type": "int", "default": "rng 10..15", "valid": "8..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "2", "valid": "2..2"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "wall_corridors_with_2_seeds",
                       "valid": "wall_corridors_with_2_seeds"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 1 red(2) seed, exactly 1 green(3) seed; gray(5) walls present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    red_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    green_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 3)
    gray_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 5)
    if red_count != 1:
        errs.append(f"expected exactly 1 red(2) seed; found {red_count}")
    if green_count != 1:
        errs.append(f"expected exactly 1 green(3) seed; found {green_count}")
    if gray_count < 2:
        errs.append(f"expected gray(5) walls; found {gray_count} gray cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 14, 15)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 10, 15)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    wall_col = w // 2
    gap = rng.randint(2, h - 3)
    for r in range(1, h - 1):
        if r != gap:
            g[r][wall_col] = 5
    for c in range(1, wall_col):
        if c not in {2, wall_col - 1}:
            g[h // 2][c] = 5
    for c in range(wall_col + 1, w - 1):
        if c not in {wall_col + 1, w - 3} and rng.choice([True, False]):
            g[min(h - 2, h // 2 + 1)][c] = 5
    g[rng.randint(2, h - 3)][1] = 2
    g[rng.randint(2, h - 3)][w - 2] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 12
    g = full_grid(h, w, 0)
    if name == "no_walls":
        # no walls → corridor structure absent, becomes plain 2-source Voronoi
        g[5][1] = 2
        g[5][w - 2] = 3
        return g
    if name == "single_seed":
        # only 1 seed → entire reachable region becomes that color (no comparison)
        wall_col = w // 2
        for r in range(1, h - 1):
            if r != 5: g[r][wall_col] = 5
        g[5][1] = 2
        return g
    if name == "no_seeds":
        # walls but no seeds → no Voronoi sources
        wall_col = w // 2
        for r in range(1, h - 1):
            if r != 5: g[r][wall_col] = 5
        return g
    return g
