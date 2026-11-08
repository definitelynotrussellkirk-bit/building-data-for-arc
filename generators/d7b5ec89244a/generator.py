"""Generator for arc_additional_puzzles_21_set22_bundle:E154.

Rule: interleaved all-zero rows are removed while colored rows are
preserved.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_marks, all_blank, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d7b5ec89244a"
VERSION = "2.0.0"
TASK_ID = "d7b5ec89244a"
SUMMARY = (
    "Grid (h~7-10, w~5-8) with 3 COLORED ROWS interleaved "
    "with all-zero rows. Each colored row has 2 non-zero "
    "cells at specific positions (col i and col w-1-i) in 3 "
    "distinct colors. Rule: filter the rows — keep only rows "
    "with at least one non-zero cell. Output: a 3 × w grid "
    "consisting of the original colored rows in their order, "
    "with all-zero rows DROPPED."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "≥2 rows entirely zero",
    "≥2 rows contain nonzero cells",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marks", "all_blank", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "7..10"},
    "grid_w":         {"type": "int", "default": "rng 5..8", "valid": "5..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_marks|all_blank|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 5, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 7, 8)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 5, 8)
    colors = list(ctx.draw_distinct_colors("colors", n=3, exclude=[0]))
    g = full_grid(h, w, 0)
    rows = [1, h // 2, h - 2]
    for i, r in enumerate(rows):
        g[r][i] = colors[i]
        g[r][w - 1 - i] = colors[i]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 6, 0)
    if name == "no_marks":
        return g
    if name == "all_blank":
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(6):
                g[r][c] = 3
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariant check for the zero-row filtering task."""
    errs = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a non-empty rectangular list-of-lists"]
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]

    zero_rows = [r for r, row in enumerate(grid) if all(v == 0 for v in row)]
    marked_rows = [r for r, row in enumerate(grid) if any(v != 0 for v in row)]
    if len(zero_rows) < 2:
        errs.append(f"expected at least two all-zero rows, found {len(zero_rows)}")
    if len(marked_rows) != 3:
        errs.append(f"expected exactly three nonzero rows, found {len(marked_rows)}")

    colors = []
    for idx, r in enumerate(marked_rows):
        nz = [(c, v) for c, v in enumerate(grid[r]) if v != 0]
        row_colors = {v for _, v in nz}
        if len(nz) not in (1, 2):
            errs.append(f"marked row {r} should contain one center cell or two mirrored cells, found {len(nz)}")
        if len(row_colors) != 1:
            errs.append(f"marked row {r} should use one color, found {sorted(row_colors)}")
        if nz:
            colors.append(nz[0][1])
        if len(nz) == 1 and nz[0][0] != w // 2:
            errs.append(f"single marked cell in row {r} should be at center column {w // 2}, found {nz[0][0]}")
        if len(nz) == 2 and nz[0][0] + nz[1][0] != w - 1:
            errs.append(f"marked row {r} cells should occupy mirrored columns, found {[c for c, _ in nz]}")
        if idx and r <= marked_rows[idx - 1]:
            errs.append("marked rows must preserve top-to-bottom order")
    if len(colors) != len(set(colors)):
        errs.append(f"the three marked rows should use distinct colors, got {colors}")
    return errs
