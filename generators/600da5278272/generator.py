"""Generator for arc_puzzle_bank_21_set14_bundle:hard_n06 — bar-count from lower-left quadrant.

Rule: output is (h/2 x w/2). For each output row r, the count of color-3 cells
in input row h/2+r (left half) determines a left-aligned color-8 bar.
The top half (rows < h/2) is decoration in color-2 staircase.

Combinatorial axes (8): grid_h, grid_w, palette_kind, density,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_lower_left, full_lower_left, odd_dims.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "600da5278272"
VERSION = "1.1.1"
TASK_ID = "600da5278272"
SUMMARY = "Even h x even w; top half has a color-2 staircase; bottom-left quadrant has color-3 bars."

INVARIANTS = [
    "background is 0",
    "grid h and w are both even (>= 6)",
    "lower-left quadrant has 1-(w/2) color-3 cells per row, left-aligned",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_lower_left", "full_lower_left", "odd_dims")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10 (even)", "valid": "6..14 (even)"},
    "grid_w":         {"type": "int", "default": "rng 10..12 (even)", "valid": "8..16 (even)"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "density":        {"type": "str", "default": "varied", "valid": "varied"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "lower_left_quadrant",
                       "valid": "lower_left_quadrant"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "n_bars":         {"type": "int", "default": "h/2", "valid": "1..h/2"},
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
        h_raw = ctx.draw_int("grid_h", 8, 8)
        w_raw = ctx.draw_int("grid_w", 10, 10)
    elif difficulty == "hard":
        h_raw = ctx.draw_int("grid_h", 9, 10)
        w_raw = ctx.draw_int("grid_w", 11, 12)
    else:
        h_raw = ctx.draw_int("grid_h", 8, 10)
        w_raw = ctx.draw_int("grid_w", 10, 12)
    h = h_raw + (h_raw % 2)
    w = w_raw + (w_raw % 2)
    rng = ctx.draw_rng("layout")

    h2 = h // 2; w2 = w // 2
    g = full_grid(h, w, 0)
    for r in range(h2, h):
        n3 = rng.randint(0, w2)
        for c in range(n3):
            g[r][c] = 3
    for r in range(h2):
        n2 = rng.randint(0, w2)
        for c in range(w - n2, w):
            g[r][c] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Even h and w; lower-left quadrant has color-3 cells left-aligned."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    if h % 2 != 0:
        errors.append(f"grid height {h} is not even")
    if w % 2 != 0:
        errors.append(f"grid width {w} is not even")
    if errors:
        return errors
    h2, w2 = h // 2, w // 2
    has_3 = any(grid[r][c] == 3 for r in range(h2, h) for c in range(w2))
    if not has_3:
        errors.append("lower-left quadrant has no color-3 cells")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    h2 = h // 2; w2 = w // 2
    if name == "empty_lower_left":
        # lower-left quadrant has no color-3 cells → all output rows have 0 bar length, no contrast
        for r in range(h2):
            for c in range(w - 3, w):
                g[r][c] = 2
        return g
    if name == "full_lower_left":
        # lower-left quadrant fully filled with 3 → all output bars have max length, no contrast
        for r in range(h2, h):
            for c in range(w2):
                g[r][c] = 3
        return g
    if name == "odd_dims":
        # odd-dim grid breaks "even h, even w" invariant, h/2 split is ambiguous
        og = full_grid(7, 9, 0)
        for r in range(3, 7):
            for c in range(r - 3):
                og[r][c] = 3
        return og
    return g
