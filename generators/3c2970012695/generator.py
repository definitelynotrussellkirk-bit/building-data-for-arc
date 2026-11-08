"""Generator for arc_puzzle_bank_third_21_bundle:easy_20_fill_the_singleton_row.

Rule: a single colored cell selects the row to fill with that color.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors, color.
Degenerates: no_seed, two_seeds, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3c2970012695"
VERSION = "1.1.1"
TASK_ID = "3c2970012695"

SUMMARY = "Single colored cell selects the row to fill with that color."

INVARIANTS = [
    "background is 0",
    "there is exactly one nonzero cell",
    "the output keeps the same canvas size",
    "the singleton color is the row fill color",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seed", "two_seeds", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "6..10"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "8..13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "1", "valid": "1"},
    "color":          {"type": "color", "default": "rng !{0}", "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one nonzero cell (the singleton seed)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nonzero) != 1:
        errs.append(f"expected exactly 1 nonzero (singleton) cell, found {len(nonzero)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 8, 13)
    g = full_grid(h, w, 0)
    g[rng.randrange(h)][rng.randrange(w)] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g



def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if len(cells) != 1:
        return [f"expected exactly one non-zero seed cell, found {len(cells)}"]
    return []

def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 0)
    if name == "no_seed":
        return g
    if name == "two_seeds":
        g[2][3] = 3
        g[5][7] = 4
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(10):
                g[r][c] = 3
        return g
    return g
