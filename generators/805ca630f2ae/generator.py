"""Generator for arc_additional_puzzle_bank_volume17:M114.

Rule: find 9-divider (row or col); for each 2-cell, mirror across
divider; if target is 0, paint 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, source_on_right, source_on_divider.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "805ca630f2ae"
VERSION = "1.1.1"
TASK_ID = "805ca630f2ae"
SUMMARY = "9-col divider + 2-3 2-cells on left + decoration on right."

INVARIANTS = [
    "exactly one full-column 9-divider",
    "2-3 2-cells on left side",
    "no 2-cells on right side",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "source_on_right", "source_on_divider")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "left_of_divider",
                       "valid": "left_of_divider"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 full-height color-9 divider column; ≥1 color-2 cell to its left."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not dividers:
        return ["expected ≥1 full-height color-9 divider column; found none"]
    first_div = min(dividers)
    has_two = any(grid[r][c] == 2 for r in range(h) for c in range(first_div))
    if not has_two:
        return ["expected ≥1 color-2 cell left of the divider; found none"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    div = w // 2
    for r in range(h):
        g[r][div] = 9
    n = rng.randint(2, 3)
    placed = 0
    while placed < n:
        r = rng.randint(1, h - 1); c = rng.randint(0, div - 1)
        if g[r][c] != 0: continue
        g[r][c] = 2; placed += 1
    g[h - 1][w - 1] = 7
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # no full 9-column → mirror axis is undefined
        g[1][1] = 2; g[3][2] = 2
        return g
    div = w // 2
    for r in range(h):
        g[r][div] = 9
    if name == "source_on_right":
        # all 2-cells on the right side → "left source" assumption violated
        g[1][div + 2] = 2; g[3][div + 3] = 2
        return g
    if name == "source_on_divider":
        # 2-cell sits on the divider column → ambiguous which side it belongs to
        g[1][div] = 2
        g[3][1] = 2
        return g
    return g
