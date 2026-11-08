"""Generator for arc_additional_puzzles_21_set4:E25.

Rule: keep only columns that have ≥1 non-zero cell; drop fully-zero
columns. Output rows project to those kept columns.

Combinatorial axes (8): grid_h/w, palette_kind, n_keep, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_zero_cols, no_kept_cols, all_zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e52b8ee307e1"
VERSION = "2.1.0"  # output width = number of kept (non-empty) columns, but n_keep was hardcoded rng 3-4 -> output width barely varied (out_shapes 6). Vary n_keep by difficulty (2..7, always < w so columns are actually dropped) and allow more active cells per column.
TASK_ID = "e52b8ee307e1"
SUMMARY = (
    "0-bg grid (h×w, h=4..6, w=7..9) with SPARSE non-zero cells. "
    "3-4 columns are 'active' (have ≥1 non-zero cell at random "
    "rows in random non-zero colors). Other columns are entirely "
    "zero (the columns-to-drop). Active cell colors drawn from "
    "varied palette. Rule: iterate over columns. Keep only "
    "columns where at least one cell is non-zero. Output: each "
    "row projected to the kept columns only (in original column "
    "order). Output height = h (unchanged); width = number of "
    "active columns."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 3-4 columns have ≥1 non-zero cell (kept)",
    "the remaining columns are entirely zero (dropped)",
    "rows preserve order; only column projection happens",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("no_zero_cols", "no_kept_cols", "all_zero")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|rainbow"},
    "n_keep":         {"type": "int", "default": "rng 3..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "low", "valid": "low"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|rainbow|no_zero_cols|no_kept_cols|all_zero"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 7, 9)
        keep_lo, keep_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 10, 13)
        keep_lo, keep_hi = 4, 7
    else:
        h = ctx.draw_int("grid_h", 4, 7)
        w = ctx.draw_int("grid_w", 8, 11)
        keep_lo, keep_hi = 3, 5
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    # always keep < w columns so some are actually dropped (rule must project)
    n_keep = min(rng.randint(keep_lo, keep_hi), w - 1)
    keep_cols = rng.sample(range(w), n_keep)
    palette = [2, 3, 4, 5, 6, 7, 8, 9]
    for c in keep_cols:
        cnt = rng.randint(1, max(1, h - 1))   # 1..h-1 active cells in this column
        rs = rng.sample(range(h), cnt)
        for r in rs:
            g[r][c] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 8
    g = full_grid(h, w, 0)
    if name == "no_zero_cols":
        # every column has a cell — output equals input (rule trivial)
        for c in range(w):
            g[c % h][c] = ((c % 7) + 2)
        return g
    if name == "no_kept_cols":
        # all columns fully zero — output has zero columns (degenerate shape)
        return g
    if name == "all_zero":
        # alias of empty — extreme of the no_kept case
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    h, w = len(grid), len(grid[0])
    active = [c for c in range(w) if any(grid[r][c] != 0 for r in range(h))]
    lo, hi = (2, 3) if difficulty == "easy" else ((4, 7) if difficulty == "hard" else (3, 5))
    if not (lo <= len(active) <= hi):
        errors.append(f"expected {lo}..{hi} active columns, got {len(active)}")
    if len(active) >= w:
        errors.append("expected at least one all-zero column to be dropped")
    return errors
