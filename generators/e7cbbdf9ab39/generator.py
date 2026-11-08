"""Generator for 7b:m43 — marked rowcol crossings.

Rule: column markers (color 3) on top+bottom borders pair up; row
markers (color 2) on left+right borders pair up. At every (row,col)
crossing of paired markers, place an 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cols, n_rows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: unpaired_col, unpaired_row, no_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e7cbbdf9ab39"
VERSION = "2.2.0"  # add executable marker-pair invariants and align axis docs with widened hard ranges
TASK_ID = "e7cbbdf9ab39"
SUMMARY = (
    "0-bg grid (size varies by difficulty) with: (a) "
    "COLUMN MARKERS — 1-5 columns in range "
    "[1, w-2] are marked by COLOR 3 (green) "
    "cells at BOTH row 0 AND row h-1 of the "
    "same column (full top+bottom pair); "
    "(b) ROW MARKERS — 1-5 rows in range "
    "[1, h-2] are marked by COLOR 2 (red) "
    "cells at BOTH col 0 AND col w-1 of the "
    "same row (full left+right pair). All "
    "marker columns and rows are interior "
    "(≥2 cells from each edge). All other "
    "cells are bg-0. Rule (AT EVERY (ROW, "
    "COL) CROSSING OF PAIRED MARKERS, PLACE "
    "COLOR 8): identify the SET of PAIRED "
    "COLUMNS (those with color-3 at both top "
    "and bottom). identify the SET of "
    "PAIRED ROWS (those with color-2 at "
    "both left and right). For EACH (r, c) "
    "with r ∈ paired rows AND c ∈ paired "
    "cols: PAINT cell (r, c) with COLOR 8 "
    "(cyan). The original markers stay; "
    "other cells stay bg-0. Net: every "
    "intersection of a marked row and "
    "marked column becomes a cyan dot, "
    "drawing the row × column lattice of "
    "crossings."
)

INVARIANTS = [
    "background is 0",
    "1-5 columns have a 3 in row 0 AND row h-1",
    "1-5 rows have a 2 in col 0 AND col w-1",
    "markers are paired and lie on the four borders only",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("unpaired_col", "unpaired_row", "no_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..14", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..15", "valid": "7..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cols":         {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "n_rows":         {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..4"},
    "position_bias":  {"type": "str", "default": "border_pairs",
                       "valid": "border_pairs"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    bad = sorted({v for row in grid for v in row if v not in (0, 2, 3)})
    if bad:
        errors.append(f"unexpected colors {bad}; expected only 0/2/3 in input")

    paired_cols = [c for c in range(1, w - 1)
                   if grid[0][c] == 3 and grid[h - 1][c] == 3]
    paired_rows = [r for r in range(1, h - 1)
                   if grid[r][0] == 2 and grid[r][w - 1] == 2]
    if not (1 <= len(paired_cols) <= 5):
        errors.append(f"expected 1..5 paired color-3 columns, found {len(paired_cols)}")
    if not (1 <= len(paired_rows) <= 5):
        errors.append(f"expected 1..5 paired color-2 rows, found {len(paired_rows)}")

    for c in range(w):
        if (grid[0][c] == 3) != (grid[h - 1][c] == 3):
            errors.append(f"unpaired color-3 column marker at col {c}")
            break
    for r in range(h):
        if (grid[r][0] == 2) != (grid[r][w - 1] == 2):
            errors.append(f"unpaired color-2 row marker at row {r}")
            break

    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] in (2, 3):
                errors.append("interior marker cell found away from border")
                return errors
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8); w = ctx.draw_int("grid_w", 8, 9)
        n_lo, n_hi = 1, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 15)
        n_lo, n_hi = 3, 5
    else:
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 10, 12)
        n_lo, n_hi = 2, 3
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # interior marker positions: cols in [1, w-2], rows in [1, h-2] (rule's range)
    col_slots = list(range(1, w - 1))
    row_slots = list(range(1, h - 1))
    n_cols = min(int(ctx.draw_int("n_cols", n_lo, n_hi)), len(col_slots))
    n_rows = min(int(ctx.draw_int("n_rows", n_lo, n_hi)), len(row_slots))
    cols = rng.sample(col_slots, n_cols)
    rows = rng.sample(row_slots, n_rows)
    for c in cols:
        g[0][c] = 3; g[h - 1][c] = 3
    for r in rows:
        g[r][0] = 2; g[r][w - 1] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "unpaired_col":
        # column 3 only on top, missing on bottom → no pair, no crossing
        g[0][3] = 3
        g[3][0] = 2; g[3][w - 1] = 2
        return g
    if name == "unpaired_row":
        # row 2 only on left, missing on right → no pair, no crossing
        g[0][3] = 3; g[h - 1][3] = 3
        g[3][0] = 2
        return g
    if name == "no_markers":
        # blank → no crossings, output identical to input
        return g
    return g
