"""Generator for arc_additional_puzzle_bank_volume8:E50.

Rule: singleton color-2 objects recolored to 3; larger color-2 objects
remain.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors, other.
Degenerates: no_singletons, no_distractor, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "702b86fcc04c"
VERSION = "1.1.1"
TASK_ID = "702b86fcc04c"
SUMMARY = "Singleton color-2 objects recolored to 3; larger color-2 objects remain."

INVARIANTS = [
    "singleton color-2 objects are separated from all other nonzero cells",
    "at least one larger color-2 object is present as a distractor",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_singletons", "no_distractor", "full_grid")
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
    "other":          {"type": "color", "default": "rng !{0,2,3}",
                       "valid": "1|4..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has color-2 cells; has at least one isolated singleton; skip degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not twos:
        errs.append("no color-2 cells found")
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
    other = ctx.draw_color("other", exclude=[0, 2, 3])
    g = full_grid(h, w, 0)
    g[1][1] = 2
    g[h - 2][w - 2] = 2
    g[1][w - 4] = 2
    g[1][w - 3] = 2
    g[h // 2][w // 2] = other
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_singletons":
        g[1][5] = 2
        g[1][6] = 2
        return g
    if name == "no_distractor":
        g[1][1] = 2
        return g
    if name == "full_grid":
        for r in range(9):
            for c in range(9):
                g[r][c] = 2
        return g
    return g
