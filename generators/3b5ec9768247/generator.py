"""Generator for arc_puzzle_bank_ninth21:E61.

Rule: four same-color corner markers define a hollow rectangle border.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors, color.
Degenerates: no_corners, single_corner, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3b5ec9768247"
VERSION = "2.0.1"
TASK_ID = "3b5ec9768247"

SUMMARY = (
    "0-bg grid (h×w, ~7-10 by ~8-12) with exactly 4 non-zero cells "
    "all of the SAME color, placed at the 4 corners of an axis-"
    "aligned rectangle (r1, c1), (r1, c2), (r2, c1), (r2, c2). "
    "The rectangle has h ≥ 3 and w ≥ 3 (so the border is "
    "visible). Rule: collect all non-zero cells, read their "
    "common color, compute bbox. Build output: fresh 0-canvas "
    "with a HOLLOW RECTANGLE (border only, interior 0) drawn at "
    "the bbox in that color. The 4 input corners are preserved; "
    "edge cells between them are filled in."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 4 non-zero cells, all the same color",
    "cells form 4 corners of an axis-aligned rectangle",
    "rectangle has h ≥ 3 AND w ≥ 3 (non-degenerate border)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_corners", "single_corner", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "7..10"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "8..12"},
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
    """Verify: bg=0, exactly 4 nonzero cells all same color forming a rectangle."""
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
    if len(nonzero) != 4:
        errs.append(f"expected 4 nonzero cells, found {len(nonzero)}")
        return errs
    colors = {grid[r][c] for r, c in nonzero}
    if len(colors) != 1:
        errs.append(f"nonzero cells have {len(colors)} distinct colors, expected 1")
    rs = sorted({r for r, c in nonzero})
    cs = sorted({c for r, c in nonzero})
    if len(rs) != 2 or len(cs) != 2:
        errs.append("4 nonzero cells do not form an axis-aligned rectangle corner set")
    elif rs[1] - rs[0] < 2 or cs[1] - cs[0] < 2:
        errs.append(f"rectangle too small: h={rs[1]-rs[0]}, w={cs[1]-cs[0]} (need >=2 each)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
    g = full_grid(h, w, 0)
    r1 = rng.randint(0, h - 4)
    r2 = rng.randint(r1 + 2, h - 1)
    c1 = rng.randint(0, w - 4)
    c2 = rng.randint(c1 + 2, w - 1)
    color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    for r, c in [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]:
        g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 0)
    if name == "no_corners":
        return g
    if name == "single_corner":
        g[2][3] = 3
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(10):
                g[r][c] = 3
        return g
    return g
