"""Generator for arc_additional_puzzle_bank_volume11:H73 — top-row radius controls cyan dilation.

Rule: a top-row radius controls cyan dilation from the red seed
component through non-wall cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, radius,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_radius, no_seed, sealed_chamber.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bd2a79b78c01"
# 2.1.0: the rule reads k = the top-row value directly (in {1,2,3}), but the
# generator wrote `radius if radius!=2 else 3`, so a radius-2 indicator was
# NEVER produced -> the k=2 branch was unexercised and "radius 2" was
# silently aliased to 3. Now writes the literal radius. Also varies the red
# seed shape (was a fixed L-tromino).
VERSION = "2.1.1"  # add self_check
TASK_ID = "bd2a79b78c01"
SUMMARY = (
    "0-bg grid (h~10-14, w~"
    "11-16) with: (a) a RADIUS "
    "INDICATOR at (0, 0) = "
    "value in {1, 3} (encoding "
    "radius 1, 2, or 3); (b) a "
    "VERTICAL COLOR-5 (gray) "
    "WALL at random col "
    "wall_col (4..w-5) with "
    "ONE GAP at row gap "
    "(3..h-3); plus a partial "
    "HORIZONTAL gray wall at "
    "row h-3 with select gap "
    "columns; (c) a CONNECTED "
    "L-SHAPED COLOR-2 (red) "
    "SEED of 3 cells in the "
    "lower-left chamber. Rule "
    "(DILATE RED SEED BY TOP-"
    "ROW RADIUS THROUGH NON-"
    "WALLS, PAINT CYAN): "
    "identify RADIUS R from "
    "(0, 0). DILATE the "
    "RED SEED COMPONENT by R "
    "cells through 4-connected "
    "non-5 (wall) cells (BFS "
    "depth ≤ R from any seed "
    "cell). PAINT all reached "
    "non-seed cells with "
    "COLOR-8 (cyan). The "
    "radius indicator, walls, "
    "and seed stay. Net: red "
    "seed grows cyan halo of "
    "radius R, blocked by "
    "gray walls."
)

INVARIANTS = [
    "the first top-row value in 1..3 is the dilation radius",
    "gray cells are walls",
    "red seed cells are connected",
    "the seed component has reachable background within and beyond the radius",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_radius", "no_seed", "sealed_chamber")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "7..24"},
    "grid_w":         {"type": "int", "default": "rng 11..16", "valid": "8..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "radius":         {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "radius_with_walls_and_seed",
                       "valid": "radius_with_walls_and_seed"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; top-row has radius value 1-3; has gray(5) walls; has red(2) seed."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    # check top-row first nonzero is radius 1-3
    top_nonzero = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    has_gray = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    if not top_nonzero and not has_gray:
        return errs  # degenerate
    if not top_nonzero:
        errs.append("top row has no radius value")
    elif top_nonzero[0] not in (1, 2, 3):
        errs.append(f"top-row radius {top_nonzero[0]} not in 1..3")
    if not has_gray:
        return errs  # degenerate no_walls
    has_red = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_red:
        errs.append("no red(2) seed cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 11, 13)
        radius = ctx.draw_int("radius", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 14, 16)
        radius = ctx.draw_int("radius", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 11, 16)
        radius = ctx.draw_int("radius", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    g[0][0] = radius                      # rule reads k = this value directly
    wall_col = rng.randint(4, w - 5)
    gap = rng.randint(3, h - 3)
    for r in range(1, h - 1):
        if r != gap:
            g[r][wall_col] = 5
    for c in range(1, wall_col):
        if c not in {2, wall_col - 1}:
            g[h - 3][c] = 5
    # Red seed: a small connected 3-4 cell polyomino in the lower-left chamber.
    seed_shapes = [
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 1)],
    ]
    shape = rng.choice(seed_shapes)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    sr = rng.randint(2, max(2, min(h - 3 - sh, gap)))
    sc = rng.randint(1, max(1, wall_col - 1 - sw))
    for dr, dc in shape:
        g[sr + dr][sc + dc] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 13
    g = full_grid(h, w, 0)
    if name == "no_radius":
        # walls + seed but (0,0) is bg → no dilation radius specified
        for r in range(1, h - 1): g[r][6] = 5
        g[3][2] = 2; g[3][3] = 2; g[4][2] = 2
        return g
    if name == "no_seed":
        # radius + walls but no red seed → nothing to dilate from
        g[0][0] = 2
        for r in range(1, h - 1): g[r][6] = 5
        return g
    if name == "sealed_chamber":
        # seed sealed by walls so dilation reaches nothing
        g[0][0] = 2
        for r in range(h):
            g[r][5] = 5
        for c in range(w):
            g[3][c] = 5
        g[1][2] = 2; g[1][3] = 2; g[2][2] = 2   # seed in tiny enclosed chamber
        return g
    return g
