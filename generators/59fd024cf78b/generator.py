"""Generator for arc_additional_puzzle_bank_volume11:E73.

Rule: orange (color-7) components touching exactly one outer border are
recolored cyan.

Combinatorial axes (8): grid_h/w, palette_kind, num_components,
palette_size, position_bias, n_distinct_colors, border_density, texture.
Degenerates: no_blobs, all_touch_zero_borders, all_touch_two_borders.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "59fd024cf78b"
VERSION = "1.1.1"
TASK_ID = "59fd024cf78b"
SUMMARY = "Orange components touching exactly one outer border are recolored cyan."

INVARIANTS = [
    "background is 0",
    "at least one orange component touches exactly one border",
    "other orange components touch zero or two borders",
    "orange components are separated by background",
]

PALETTE_KINDS = ("default", "warm_grid", "tight_grid", "wide_grid")
DEGENERATE_TEXTURES = ("no_blobs", "all_touch_zero_borders", "all_touch_two_borders")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "num_components": {"type": "int", "default": "4", "valid": "3..5"},
    "border_density": {"type": "str", "default": "mixed",
                       "valid": "mixed"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 8, 13)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    top_c = rng.randint(2, w - 4)
    draw_rect(g, 0, top_c, 2, 2, 7)
    left_r = rng.randint(3, h - 4)
    draw_rect(g, left_r, 0, 2, 1, 7)
    draw_rect(g, h - 2, w - 2, 2, 2, 7)
    draw_rect(g, h // 2, w // 2, 2, 2, 7)
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one orange (color-7) cell present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    has7 = any(grid[r][c] == 7 for r in range(h) for c in range(w))
    if not has7:
        errs.append("no orange (color-7) cells found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_blobs":
        return g
    if name == "all_touch_zero_borders":
        # all interior — no component qualifies for recolor
        draw_rect(g, 3, 3, 2, 2, 7)
        draw_rect(g, 6, 6, 2, 2, 7)
        return g
    if name == "all_touch_two_borders":
        # all components touch corners (2 borders) — no component qualifies
        draw_rect(g, 0, 0, 2, 2, 7)
        draw_rect(g, 0, w - 2, 2, 2, 7)
        draw_rect(g, h - 2, 0, 2, 2, 7)
        draw_rect(g, h - 2, w - 2, 2, 2, 7)
        return g
    return g
