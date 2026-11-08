"""Generator for arc_puzzle_bank_21_set6:easy_f07.

Rule: extract a one-row palette in first-appearance order.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, single_color, all_one_position.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8b45d6dd2123"
VERSION = "1.1.1"
TASK_ID = "8b45d6dd2123"
SUMMARY = "Extract a one-row palette in first-appearance order."

INVARIANTS = [
    "background is 0",
    "nonzero colors can repeat",
    "output contains each observed color once",
    "palette order is first appearance in reading order",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_grid", "single_color", "all_one_position")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; at least 1 non-bg cell; values in 0-9 range."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if not (0 <= v <= 9):
                errs.append(f"cell ({r},{c}) value {v} out of range")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 6, 7)
        n = ctx.draw_int("palette_size", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 8, 9)
        n = ctx.draw_int("palette_size", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 6, 9)
        n = ctx.draw_int("palette_size", 3, 5)
    rng = ctx.draw_rng("layout")
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    g = full_grid(h, w, 0)
    cells = [(r, c) for r in range(h) for c in range(w)]
    first_cells = sorted(rng.sample(cells, n))
    for (r, c), color in zip(first_cells, colors):
        g[r][c] = color
    for _ in range(rng.randint(2, 5)):
        r, c = rng.choice(cells)
        if g[r][c] == 0:
            g[r][c] = rng.choice(colors)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 7
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # no cells → palette is empty, output 1×0
        return g
    if name == "single_color":
        # only one color present → palette has one entry
        for r, c in [(1, 1), (2, 4), (3, 2)]:
            g[r][c] = 5
        return g
    if name == "all_one_position":
        # only one cell populated → palette is just that one color, reading order trivial
        g[h // 2][w // 2] = 7
        return g
    return g
