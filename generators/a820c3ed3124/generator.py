"""Generator for arc_additional_puzzle_bank_volume17:M116 — Flood-fill bg around red seed.

Rule: connected-region from the (single) red(2) seed through bg cells.
Paint all bg cells in the reached region with 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_walls,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls, no_seed, seed_in_wall.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a820c3ed3124"
VERSION = "1.1.0"
TASK_ID = "a820c3ed3124"
SUMMARY = "Gray walls forming compartments; red seed inside one + green distractor in another; flood with 8."

INVARIANTS = [
    "outer border all gray(5)",
    "≥1 vertical gray wall splits interior into ≥2 compartments",
    "exactly one red(2) seed in left compartment",
    "(optional) one distractor non-bg cell in right compartment (won't affect output)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_seed", "seed_in_wall")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_walls":        {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "framed_with_walls_and_seed",
                       "valid": "framed_with_walls_and_seed"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "framed", "valid": "framed"},
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
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 9, 14)
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][0] = 5; g[r][w-1] = 5
    for c in range(w):
        g[0][c] = 5; g[h-1][c] = 5
    rng = ctx.draw_rng("walls")
    n_walls = rng.randint(1, 2)
    cols_used = []
    for _ in range(n_walls):
        for _ in range(20):
            col = rng.randint(2, w - 3)
            if all(abs(col - c) >= 2 for c in cols_used):
                cols_used.append(col)
                for r in range(h): g[r][col] = 5
                break
    sr = rng.randint(1, h - 2)
    sc = rng.randint(1, min(cols_used) - 1) if cols_used else rng.randint(1, w - 2)
    g[sr][sc] = 2
    if cols_used and rng.random() < 0.5:
        last_col = max(cols_used)
        for _ in range(15):
            r = rng.randint(1, h - 2); c = rng.randint(last_col + 1, w - 2)
            if g[r][c] == 0:
                g[r][c] = rng.choice([3, 4, 6, 7])
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 11
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][0] = 5; g[r][w - 1] = 5
    for c in range(w):
        g[0][c] = 5; g[h - 1][c] = 5
    if name == "no_walls":
        # bordered grid with no interior walls → flood fills entire interior with 8
        g[3][5] = 2
        return g
    if name == "no_seed":
        # walls but no red seed → flood has no source, rule fires zero times
        for r in range(h):
            g[r][4] = 5
        return g
    if name == "seed_in_wall":
        # red seed lands on a wall cell → ambiguous semantics (cell is both wall and seed)
        for r in range(h):
            g[r][4] = 5
        g[3][4] = 2   # seed embedded in wall
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if h < 5 or w < 8:
        errors.append(f"grid too small for chamber flood-fill: {h}x{w}")
    if any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)):
        errors.append("top and bottom borders must be gray(5) walls")
    if any(grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)):
        errors.append("left and right borders must be gray(5) walls")
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(seeds) != 1:
        errors.append(f"expected exactly one red(2) seed, found {len(seeds)}")
    else:
        sr, sc = seeds[0]
        if sr in (0, h - 1) or sc in (0, w - 1):
            errors.append("red seed must be inside the gray border")
        if not any(0 <= sr + dr < h and 0 <= sc + dc < w and grid[sr + dr][sc + dc] == 0
                   for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            errors.append("red seed should touch at least one flood-fillable black(0) cell")
    interior_wall_cols = [c for c in range(1, w - 1)
                          if all(grid[r][c] == 5 for r in range(h))]
    if not interior_wall_cols:
        errors.append("expected at least one full-height interior gray(5) wall")
    if any(v < 0 or v > 9 for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    return errors

