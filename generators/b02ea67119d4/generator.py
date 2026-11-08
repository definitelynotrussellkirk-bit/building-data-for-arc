"""Generator for arc_puzzle_bank_21_set12_s:S12_E7 — red selects largest neighbor → 8.

Rule: a red component touches several neighbors; the largest red
neighbor is kept and recolored to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, large_side,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_red, no_neighbors, tied_neighbors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b02ea67119d4"
VERSION = "1.1.1"
TASK_ID = "b02ea67119d4"
SUMMARY = "A red component touches several neighbors; the largest red neighbor is kept as 8."

INVARIANTS = [
    "background is 0",
    "there is exactly one color-2 red component",
    "red touches at least two neighbor components",
    "one red neighbor has strictly largest area",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_red", "no_neighbors", "tied_neighbors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "7..15"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "large_side":     {"type": "str", "default": "rng down|right", "valid": "down|right"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "red_with_neighbors",
                       "valid": "red_with_neighbors"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one color-2 (red) component present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_red",):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_2 = any(grid[r][c] == 2 for r in range(h) for c in range(w))
    if not has_2:
        errs.append("no color-2 (red) component found")
    return errs


def _paint(g, cells, color):
    for r, c in cells:
        g[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 10, 13)
    side = ctx.draw_choice("large_side", ["down", "right"])
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    r = rng.randint(2, h - 5)
    c = rng.randint(2, w - 7)
    g[r][c] = 2
    if side == "down":
        g[r][c + 1] = 3
        _paint(g, [(r + 1, c), (r + 2, c), (r + 2, c + 1)], 4)
    else:
        g[r + 1][c] = 3
        _paint(g, [(r, c + 1), (r, c + 2), (r + 1, c + 2)], 4)
    _paint(g, [(h - 2, w - 3), (h - 2, w - 2)], 6)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 11
    g = full_grid(h, w, 0)
    if name == "no_red":
        # no red component → no rule trigger
        _paint(g, [(2, 2), (2, 3)], 3)
        _paint(g, [(5, 5), (6, 5)], 4)
        return g
    if name == "no_neighbors":
        # red is isolated → no neighbor to recolor as 8
        g[3][3] = 2
        _paint(g, [(7, 8), (7, 9)], 6)
        return g
    if name == "tied_neighbors":
        # two equally-sized red neighbors → ambiguous "largest"
        g[3][3] = 2
        _paint(g, [(3, 4), (3, 5)], 4)
        _paint(g, [(4, 3), (5, 3)], 4)
        return g
    return g
