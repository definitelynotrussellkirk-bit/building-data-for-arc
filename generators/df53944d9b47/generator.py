"""Generator for arc_puzzle_bank_third21:H18.

Rule: the FIRST color-7 cell's column = vertical mirror axis. For each
non-bg, non-7 cell at (r, c), output paints (r, c) and (r, 2*axis - c)
in the same color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_axis, axis_off_grid, no_cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "df53944d9b47"
VERSION = "2.0.0"
TASK_ID = "df53944d9b47"

SUMMARY = (
    "0-bg grid (h~6-14, w~8-16) with: "
    "(a) ONE COLOR-7 AXIS MARKER at "
    "column axis ∈ [2, w-3] (interior, "
    "with ≥1 col on each side), placed "
    "at random row axis_row ∈ [0, h-1] "
    "(cell (axis_row, axis) = 7); "
    "(b) 3-10 NON-BG NON-7 SOURCE "
    "CELLS placed at random distinct "
    "positions on EITHER side of the "
    "axis column (one side or "
    "scattered), each painted in a "
    "color cycling through a shuffled "
    "palette {1, 2, 3, 4, 5, 6, 8, 9}. "
    "For each source cell at (r, c), "
    "its mirror position (r, 2*axis-c) "
    "is bg-0 and in-bounds (constraint "
    "enforced). Rule (REFLECT EACH "
    "NON-BG NON-7 CELL ACROSS THE "
    "VERTICAL 7-AXIS COLUMN): find "
    "the COLOR-7 cell — its column is "
    "the AXIS. For EACH non-{0, 7} "
    "cell at (r, c) where c ≠ axis: "
    "COMPUTE the MIRROR position "
    "(r, 2*axis - c). PAINT the mirror "
    "cell with the SAME COLOR as the "
    "source (only if currently bg-0). "
    "The 7-axis marker and source "
    "cells stay. Net: every colored "
    "cell off the axis gets a mirror "
    "copy on the other side, producing "
    "left-right symmetry around the "
    "7-axis."
)

# Rivals: 'horizontal-flip whole grid' refuted by ≥1 demo where
# axis is off-center. 'use bg color for mirror' refuted by any demo
# (mirror keeps original color). 'mirror across grid center' refuted
# by ≥2 demos with off-center axis. 'erase originals after mirror'
# refuted by any demo.
# 4 demos with varied axis positions + cell counts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one color-7 cell (the axis)",
    "≥1 non-bg, non-7 cell to mirror",
    "the mirror of each cell stays in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_axis", "axis_off_grid", "no_cells")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_cells":        {"type": "int", "default": "rng 3..6", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "one_side_of_axis",
                       "valid": "one_side_of_axis"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_axis|axis_off_grid|no_cells"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 10)
        n_cells = ctx.draw_int("n_cells", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        n_cells = ctx.draw_int("n_cells", 6, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 13)
        n_cells = ctx.draw_int("n_cells", 3, 6)
    g = full_grid(h, w, 0)
    # Pick axis column. Constraint: axis must be in middle-ish range so
    # mirrors of cells on one side can fit on the other.
    # Make axis somewhere with ≥1 col on each side.
    axis = rng.randint(2, w - 3)
    # Place axis marker at random row.
    axis_row = rng.randint(0, h - 1)
    g[axis_row][axis] = 7
    # Choose a side (left or right) and place cells there.
    palette = [1, 2, 3, 4, 5, 6, 8, 9]
    rng.shuffle(palette)
    placed = 0
    for _ in range(150):
        if placed >= n_cells:
            break
        side = rng.choice(["left", "right"])
        if side == "left":
            c = rng.randint(0, axis - 1)
        else:
            c = rng.randint(axis + 1, w - 1)
        r = rng.randint(0, h - 1)
        if g[r][c] != 0:
            continue
        # Mirror position must be in-bounds and bg.
        mc = 2 * axis - c
        if not (0 <= mc < w):
            continue
        if g[r][mc] != 0 and (r, mc) != (axis_row, axis):
            continue
        g[r][c] = palette[placed % len(palette)]
        placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for vertical-axis reflection examples."""
    errs = []
    if not grid or not isinstance(grid[0], list):
        return ["grid is empty or not rectangular"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        errs.append("grid rows have inconsistent widths")
        return errs
    axes = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
    if len(axes) != 1:
        return [f"expected exactly one color-7 axis marker, found {len(axes)}"]
    axis_r, axis_c = axes[0]
    if not (1 <= axis_c <= w - 2):
        errs.append(f"axis column {axis_c} is not interior")
    sources = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 7)]
    if not sources:
        errs.append("no non-bg non-axis cells to mirror")
    for r, c, v in sources:
        if c == axis_c:
            errs.append("source cell lies on the axis column")
            continue
        mc = 2 * axis_c - c
        if not (0 <= mc < w):
            errs.append("source mirror falls out of bounds")
        elif grid[r][mc] != 0:
            errs.append("source mirror target is not background")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    if name == "no_axis":
        g[2][2] = 4; g[5][8] = 6
        return g
    if name == "axis_off_grid":
        g[2][0] = 7  # axis at col 0 — mirrors go off-grid
        g[3][1] = 4
        return g
    if name == "no_cells":
        g[3][5] = 7
        return g
    return g
