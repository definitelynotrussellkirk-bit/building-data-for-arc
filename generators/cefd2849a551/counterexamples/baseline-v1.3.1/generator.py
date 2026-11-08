"""Generator for arc_puzzle_bank_21_set6_s:S6_E2.

Rule: a single solid object is reduced to its 4-neighbor boundary.

Combinatorial axes (8): grid_h, grid_w, palette_kind, shape_kind,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_object, hollow_object, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cefd2849a551"
VERSION = "1.3.1"  # L-shape r0 used h-max(rh1,rh2); needs h-(rh1+rh2-1) → bottom rect ran off grid
TASK_ID = "cefd2849a551"

SUMMARY = "Single solid (4-connected) object on bg. Rule outputs a blank grid (same dims) with only the object's 4-neighbor boundary cells painted (object's color); interior cells become 0."

# Rivals: 'output is input' refuted by any demo with non-trivial
# interior (interior cells erased). 'use bg color for boundary'
# refuted by any demo (boundary keeps object color). 'output the
# interior, not boundary' refuted by any demo. 'use 8-neighbor
# boundary' refuted by any demo where corner cells without a 4-conn
# neighbor outside stay (rule uses 4-conn). 3 demos with varied
# shapes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "there is exactly one nonzero object",
    "the object is solid and 4-connected",
    "at least one object cell is interior and will be erased",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_object", "hollow_object", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "shape_kind":     {"type": "choice", "default": "rng rect|step|L|T", "valid": "rect|step|L|T"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "single_solid_object",
                       "valid": "single_solid_object"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_object|hollow_object|single_cell"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all values 0-9; exactly one non-zero color present."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    colors_used = {v for row in grid for v in row if v != 0}
    if not colors_used:
        return errs  # degenerate no_object — allow
    if len(colors_used) > 1:
        errs.append(f"expected single non-zero color; found {sorted(colors_used)}")
    return errs


def _draw_rect(g, r0, c0, rh, rw, color):
    for r in range(r0, r0 + rh):
        for c in range(c0, c0 + rw):
            g[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 6, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 13, 18)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 9, 13)
    shape_kind = ctx.draw_choice("shape_kind", ["rect", "step", "L", "T"])
    color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    g = full_grid(h, w, 0)
    if shape_kind == "rect":
        rh = rng.randint(3, max(3, h - 1))
        rw = rng.randint(3, max(3, w - 1))
        rh = min(rh, h - 1); rw = min(rw, w - 1)
        r0 = rng.randint(0, h - rh)
        c0 = rng.randint(0, w - rw)
        _draw_rect(g, r0, c0, rh, rw, color)
    elif shape_kind == "step":
        rh1 = rng.randint(3, min(5, max(3, h - 2)))
        rw1 = rng.randint(3, min(6, max(3, w - 3)))
        rh2 = rng.randint(2, min(4, max(2, h - rh1 + 1)))
        rw2 = rng.randint(2, min(4, max(2, w - rw1 + 1)))
        r0 = rng.randint(0, max(0, h - (rh1 + rh2 - 1)))
        c0 = rng.randint(0, max(0, w - (rw1 + rw2 - 1)))
        _draw_rect(g, r0, c0, rh1, rw1, color)
        _draw_rect(g, r0 + rh1 - 1, c0 + rw1 - 1, rh2, rw2, color)
    elif shape_kind == "L":
        rh1 = rng.randint(3, min(5, max(3, h - 1)))
        rw1 = rng.randint(2, max(2, w // 2))
        rh2 = rng.randint(2, max(2, h // 2))
        rw2 = rng.randint(3, min(6, max(3, w - 1)))
        rw1 = min(rw1, rw2); rh1 = min(rh1, h - 1)
        # The L is a vertical bar (rh1) + a horizontal bar (rh2) overlapping ONE
        # shared row, so its total height is rh1+rh2-1 — not max(rh1,rh2). Two bugs:
        # (1) r0 used `h - max(rh1,rh2)` (too low → bottom rect ran off the grid);
        # (2) rh1 and rh2 are drawn independently, so rh1+rh2-1 can EXCEED h (e.g.
        # h=6, rh1=5, rh2=3 ⇒ 7 > 6) — then even r0=0 overflows. Clamp rh2 so the
        # combined span fits (rh2 ≥ 2 preserved since rh1 ≤ h-1), then reserve the
        # full span in r0. This was the IndexError on both easy and hard.
        rh2 = min(rh2, h - rh1 + 1)
        r0 = rng.randint(0, max(0, h - (rh1 + rh2 - 1)))
        c0 = rng.randint(0, max(0, w - rw2))
        _draw_rect(g, r0, c0, rh1, rw1, color)
        _draw_rect(g, r0 + rh1 - 1, c0, rh2, rw2, color)
    else:  # T
        rh1 = rng.randint(2, max(2, h // 2))
        rw1 = rng.randint(4, min(7, max(4, w - 1)))
        rh2 = rng.randint(3, max(3, h - rh1))
        rw2 = rng.randint(2, max(2, rw1 - 2))
        r0 = rng.randint(0, max(0, h - (rh1 + rh2 - 1)))
        c0 = rng.randint(0, max(0, w - rw1))
        _draw_rect(g, r0, c0, rh1, rw1, color)
        stem_c = c0 + (rw1 - rw2) // 2
        _draw_rect(g, r0 + rh1 - 1, stem_c, rh2, rw2, color)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_object":
        # blank → no object, rule has no boundary to extract
        return g
    if name == "hollow_object":
        # already a hollow ring → no interior cells to erase, rule is identity
        for c in range(1, 6): g[1][c] = 4; g[5][c] = 4
        for r in range(1, 6): g[r][1] = 4; g[r][5] = 4
        return g
    if name == "single_cell":
        # single cell → no interior, boundary equals object (identity)
        g[3][4] = 4
        return g
    return g
