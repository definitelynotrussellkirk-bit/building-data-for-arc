"""Generator for arc_puzzle_bank_21_set11_s:S11_E6 — Reflect across vertical 5-axis.

Rule: find first column that is all 5. For each non-zero non-5 cell, if
its mirror across the axis is currently empty, paint it there.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_marks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_axis, no_marks, marks_on_axis.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "44de940bd269"
VERSION = "2.1.0"  # honor n_marks axis and fail closed on under-placement
TASK_ID = "44de940bd269"
SUMMARY = (
    "0-bg grid (h~5-8, w~9-11) with: (a) ONE "
    "FULL-HEIGHT color-5 (gray) VERTICAL AXIS at some "
    "column axis_col (chosen so reflection fits in "
    "bounds); (b) 3-5 scattered non-{0, 5} colored "
    "MARK CELLS, ~70% on the LEFT side of the axis "
    "and ~30% on the right, each placed only where "
    "its mirror cell is currently empty. Rule: for "
    "each non-zero non-5 cell at (r, c), compute "
    "mirror column mc = 2*axis_col - c. If (r, mc) "
    "is in bounds AND currently 0, PAINT (r, mc) "
    "with the same color as (r, c). The gray axis "
    "stays 5; original marks stay. Net: the gray "
    "vertical line acts as a mirror, completing the "
    "reflection of all non-axis colored cells across "
    "it."
)

INVARIANTS = [
    "exactly one full-height column of 5s",
    "≥3 non-zero non-5 cells, mostly on the left side of the axis",
    "axis-col leaves room for reflection",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_axis", "no_marks", "marks_on_axis")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_marks":        {"type": "int", "default": "rng 3..5", "valid": "3..5"},
    "palette_size":   {"type": "int", "default": "rng 2..6", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "left_marks_with_5_axis",
                       "valid": "left_marks_with_5_axis"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..6", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_axis|no_marks|marks_on_axis"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    # Pick axis_col such that reflection fits
    axis_col = rng.randint(3, w - 4)
    for r in range(h):
        g[r][axis_col] = 5
    palette = [1, 2, 3, 4, 6, 7, 8, 9]
    n_marks = ctx.draw_int("n_marks", 3, 5)
    placed = 0
    for _ in range(60):
        if placed >= n_marks:
            break
        r = rng.randint(0, h - 1)
        # Place mostly on left side (some on right too)
        if rng.random() < 0.7:
            c = rng.randint(0, axis_col - 1)
        else:
            c = rng.randint(axis_col + 1, w - 1)
        if g[r][c] == 0:
            mc = 2 * axis_col - c
            if 0 <= mc < w and g[r][mc] == 0:
                g[r][c] = rng.choice(palette)
                placed += 1
    if placed != n_marks:
        raise ValueError(f"could not place {n_marks} reflected marks")
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    axis_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(axis_cols) != 1:
        errs.append("expected exactly one full-height color-5 axis")
        return errs
    axis = axis_cols[0]
    marks = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 5)]
    if len(marks) < 3:
        errs.append("expected at least three non-axis marks")
    for r, c in marks:
        mc = 2 * axis - c
        if not (0 <= mc < w):
            errs.append(f"mark {(r, c)} has out-of-bounds mirror across axis {axis}")
        elif grid[r][mc] != 0:
            errs.append(f"mark {(r, c)} mirror cell {(r, mc)} is not blank")
    if not marks:
        errs.append("expected at least one mark with an empty in-bounds mirror cell")
    return sorted(set(errs))



def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "no_axis":
        # marks but no 5-axis → no axis to reflect across
        g[1][1] = 4; g[2][2] = 6
        return g
    if name == "no_marks":
        # axis only, no marks → nothing to mirror
        for r in range(h): g[r][5] = 5
        return g
    if name == "marks_on_axis":
        # marks on the axis column → mirror to self, no reflection signal
        for r in range(h): g[r][5] = 5
        # can't actually overwrite 5s; place neighbors
        g[1][4] = 4
        g[3][4] = 6
        return g
    return g
