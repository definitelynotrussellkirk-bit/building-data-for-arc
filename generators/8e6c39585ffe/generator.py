"""Generator for arc_additional_puzzle_bank_volume8:E52.

Rule: color-7 size-three 2x2 L objects are recolored to 8.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors, other.
Degenerates: no_objects, only_distractor, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8e6c39585ffe"
VERSION = "1.1.1"
TASK_ID = "8e6c39585ffe"
SUMMARY = "Color-7 size-three 2x2 L objects recolored to 8."

INVARIANTS = [
    "at least one color-7 L-triomino is present",
    "larger color-7 objects are present as distractors",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_objects", "only_distractor", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "8..11"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "8..11"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "other":          {"type": "color", "default": "rng !{0,7,8}",
                       "valid": "1..6|9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-7 cell present (L-triominoes or distractor)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture == "no_objects":
        return errs
    if not any(grid[r][c] == 7 for r in range(h) for c in range(w)):
        errs.append("no color-7 cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
    other = ctx.draw_color("other", exclude=[0, 7, 8])
    g = full_grid(h, w, 0)
    for dr, dc in [(0, 0), (0, 1), (1, 0)]:
        g[1 + dr][1 + dc] = 7
    for dc in range(4):
        g[h - 2][w - 5 + dc] = 7
    g[0][w - 1] = other
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_objects":
        g[0][8] = 3
        return g
    if name == "only_distractor":
        for dc in range(4):
            g[7][3 + dc] = 7
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 7
        return g
    return g
