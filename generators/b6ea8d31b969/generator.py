"""Generator for arc_puzzle_bank_seventh21:E47.

Separated 2x2 L-shapes have one missing square corner.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_squares,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_l_shapes, full_2x2, mixed_color_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b6ea8d31b969"
# 1.2.0: more L-shapes + bigger grids in hard/medium for richer instances
VERSION = "1.2.1"
TASK_ID = "b6ea8d31b969"

SUMMARY = "Separated 2x2 L-shapes have one missing square corner."

INVARIANTS = [
    "background is 0",
    "each active 2x2 window has three same-color cells",
    "the missing 2x2 corner is initially 0",
    "active windows are separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l_shapes", "full_2x2", "mixed_color_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_squares":      {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "separated_2x2_l_shapes",
                       "valid": "separated_2x2_l_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: every nonzero cell has ≥1 nonzero 4-neighbor (L-triominoes are connected)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0:
                continue
            nbrs = [grid[r + dr][c + dc]
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    if 0 <= r + dr < h and 0 <= c + dc < w]
            if not any(v != 0 for v in nbrs):
                errs.append(f"isolated nonzero cell at ({r},{c})={grid[r][c]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 6, 7)
        target = ctx.draw_int("n_squares", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 10, 14)
        target = ctx.draw_int("n_squares", 4, 7)
    else:
        h = ctx.draw_int("grid_h", 6, 11)
        w = ctx.draw_int("grid_w", 6, 11)
        target = ctx.draw_int("n_squares", 2, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    reserved: set[tuple[int, int]] = set()
    placed = 0
    for _ in range(300):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        guard = {
            (r, c)
            for r in range(max(0, r0 - 1), min(h, r0 + 3))
            for c in range(max(0, c0 - 1), min(w, c0 + 3))
        }
        if guard & reserved:
            continue
        missing = rng.choice([(0, 0), (0, 1), (1, 0), (1, 1)])
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for dr in [0, 1]:
            for dc in [0, 1]:
                if (dr, dc) != missing:
                    g[r0 + dr][c0 + dc] = color
        reserved.update(guard)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_l_shapes":
        # blank → no L-shapes to complete
        return g
    if name == "full_2x2":
        # 2x2 already full → no missing corner
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 4
        return g
    if name == "mixed_color_l":
        # 3 cells in 2x2 of 3 different colors → "three same-color" precondition fails
        g[1][1] = 4; g[1][2] = 6; g[2][1] = 7
        return g
    return g
