"""Generator for arc_additional_puzzles_21_set14_bundle:H92.

Rule: row keys = col 0 values (rows 1+); col keys = row 0 values
(cols 1+). Output 3*N rows × 3*M cols where each tile is motif
(col_key) transformed by row_key.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rows, n_cols,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_row_keys, no_col_keys, all_zero_keys.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4887320f66db"
VERSION = "3.0.2"  # in/out-shapes only 4 (n_rows,n_cols pinned to {2,3} -> output 6/9 x 6/9). Output = 3*n_rows x 3*n_cols and the rule reads any number of row/col keys, so widened n_rows,n_cols to 2..6 (output up to 18x18 <= 30) -> many more input AND output shapes.
TASK_ID = "4887320f66db"
SUMMARY = (
    "Small (n_rows+1) × (n_cols+1) key grid (normal n_rows/n_cols vary from 2 to 6; easy keeps 2-3). "
    "Row 0 (cols 1..N) holds N COL-KEYS — values in "
    "{2, 3, 4} encoding motif ids. Col 0 (rows 1..M) "
    "holds M ROW-KEYS — values in {1, 2, 3, 4} encoding "
    "transform codes. The (0, 0) cell and the interior "
    "cells are 0. Rule: output is 3M × 3N. For each "
    "(i, j) tile (i = row-key index, j = col-key index), "
    "fetch the 3×3 MOTIF identified by col-key value, "
    "apply transform indicated by row-key value (e.g., "
    "1=identity, 2=rot-CW, 3=rot-180, 4=rot-CCW), and "
    "place it in tile slot (i, j). Net: a 3M × 3N "
    "tile-mosaic of transformed motifs."
)

INVARIANTS = [
    "row 0 (cols 1+) has n_cols cells of values 2/3/4 (motif ids)",
    "col 0 (rows 1+) has n_rows cells of values 1/2/3/4 (transform codes)",
    "interior cells are all 0",
]

PALETTE_KINDS = ("default", "few_keys", "many_keys", "varied_keys")
DEGENERATE_TEXTURES = ("no_row_keys", "no_col_keys", "all_zero_keys")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "n_rows+1", "valid": "3..7"},
    "grid_w":         {"type": "int", "default": "n_cols+1", "valid": "3..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rows":         {"type": "int", "default": "rng 2..6", "valid": "2..6"},
    "n_cols":         {"type": "int", "default": "rng 2..6", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "row0_col0", "valid": "row0_col0"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n_rows = ctx.draw_int("n_rows", 2, 3)
        n_cols = ctx.draw_int("n_cols", 2, 3)
    elif difficulty == "hard":
        n_rows = ctx.draw_int("n_rows", 4, 6)
        n_cols = ctx.draw_int("n_cols", 4, 6)
    else:
        n_rows = ctx.draw_int("n_rows", 2, 5)
        n_cols = ctx.draw_int("n_cols", 2, 5)
    h = n_rows + 1; w = n_cols + 1
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    for c in range(1, w):
        g[0][c] = rng.randint(2, 4)
    for r in range(1, h):
        g[r][0] = rng.randint(1, 4)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 4, 4
    g = full_grid(h, w, 0)
    if name == "no_row_keys":
        # only col-key header — no row-transform codes, output dims undefined
        g[0][1] = 2; g[0][2] = 3; g[0][3] = 4
        return g
    if name == "no_col_keys":
        # only row-transform header — no motif ids, output dims undefined
        g[1][0] = 1; g[2][0] = 2; g[3][0] = 3
        return g
    if name == "all_zero_keys":
        # both headers exist but every key is 0 → no tiles to compose
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable key-grid invariants for the motif/transform table."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    if not (3 <= h <= 7 and 3 <= w <= 7):
        errors.append(f"normal key grid should be 3..7 in each axis, got {h}x{w}")
    if difficulty == "easy" and not (3 <= h <= 4 and 3 <= w <= 4):
        errors.append(f"easy key grid should stay canonical-small (3..4), got {h}x{w}")
    if grid[0][0] != 0:
        errors.append(f"(0,0) should be 0, found {grid[0][0]}")
    col_keys = [grid[0][c] for c in range(1, w)]
    row_keys = [grid[r][0] for r in range(1, h)]
    bad_cols = [v for v in col_keys if v not in (2, 3, 4)]
    bad_rows = [v for v in row_keys if v not in (1, 2, 3, 4)]
    if bad_cols:
        errors.append(f"col-keys should all be in {{2,3,4}}, found {bad_cols}")
    if bad_rows:
        errors.append(f"row-keys should all be in {{1,2,3,4}}, found {bad_rows}")
    interior_bad = [(r, c, grid[r][c]) for r in range(1, h) for c in range(1, w) if grid[r][c] != 0]
    if interior_bad:
        errors.append(f"interior cells must stay 0, first bad={interior_bad[0]}")
    return errors
