"""Generator for arc_additional_puzzles_21_set17_bundle:E116 — Reflect non-bg across 8-column.

Rule: find vertical 8-column. For each non-zero non-8 cell, mirror its
value across the 8-column to (r, 2*guide-c).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_marks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, no_marks, marks_on_both_sides.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "92343d94fc17"
VERSION = "2.0.1"
TASK_ID = "92343d94fc17"
SUMMARY = (
    "0-bg grid (h~6-10, w~7-11) "
    "with: (a) ONE FULL-HEIGHT "
    "COLOR-8 (cyan) DIVIDER "
    "COLUMN at col `guide_col` "
    "(random 2..(w-1)//2 — left "
    "of center so the mirror "
    "fits on the right side); "
    "(b) 4-(guide_col*h/2) "
    "non-{0, 8} CONTENT CELLS on "
    "the LEFT SIDE ONLY (cols "
    "0..guide_col-1) at random "
    "positions in ONE random "
    "color from {1..9} minus "
    "{0, 8}. Right side starts "
    "all 0. Rule (REFLECT LEFT "
    "ACROSS 8-DIVIDER): identify "
    "the cyan VERTICAL DIVIDER "
    "at col `guide`. For EACH "
    "non-bg non-8 CELL at "
    "(r, c) with c < guide, "
    "PAINT the MIRROR position "
    "(r, 2*guide - c) on the "
    "right with the SAME COLOR. "
    "Divider stays. Net: left "
    "content reflected across "
    "cyan column to right side."
)

INVARIANTS = [
    "exactly one full-height column of 8s",
    "all non-bg non-8 cells lie on the LEFT side of the 8-column",
    "≥3 non-bg non-8 cells",
    "guide-col leaves ≥guide-col cols on the right (for mirror to fit)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_marks", "marks_on_both_sides")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_marks":        {"type": "int", "default": "rng 4..8", "valid": "3..12"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "vertical_8_divider_with_left_marks",
                       "valid": "vertical_8_divider_with_left_marks"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 full-height color-8 divider col and >=1 non-{0,8} cell to its left."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_divider", "no_marks", "marks_on_both_sides"):
        return errs
    guide = next(
        (c for c in range(w) if all(grid[r][c] == 8 for r in range(h))),
        None
    )
    if guide is None:
        errs.append("no full-height color-8 divider column found")
        return errs
    left_marks = any(grid[r][c] not in (0, 8) for r in range(h) for c in range(guide))
    if not left_marks:
        errs.append("no non-{0,8} cells found to the left of the color-8 divider")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 7, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    guide_col = rng.randint(2, (w - 1) // 2)
    for r in range(h):
        g[r][guide_col] = 8
    color = rng.choice([1, 2, 3, 4, 6, 7, 9])
    n_cells = rng.randint(4, max(4, guide_col * h // 2))
    placed = 0
    for _ in range(80):
        if placed >= n_cells:
            break
        r = rng.randint(0, h - 1); c = rng.randint(0, guide_col - 1)
        if g[r][c] == 0:
            g[r][c] = color
            placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # marks without 8-divider → no axis to mirror across
        g[1][1] = 4
        g[3][2] = 4
        g[5][1] = 4
        return g
    if name == "no_marks":
        # divider alone, no marks → nothing to reflect
        for r in range(h):
            g[r][3] = 8
        return g
    if name == "marks_on_both_sides":
        # marks on both sides of divider → "left side only" precondition fails
        for r in range(h):
            g[r][3] = 8
        g[1][1] = 4
        g[3][6] = 4  # also on right side
        g[5][2] = 4
        return g
    return g
