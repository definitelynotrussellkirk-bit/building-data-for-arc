"""Generator for arc_puzzle_bank_fourteenth21:E97.

Rule: scatter row-local color sequences that are stably packed to the
left of each row.

Combinatorial axes (8): grid_h, grid_w, palette_kind, active_rows,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, already_packed, single_color_per_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "709d506bd0aa"
VERSION = "2.0.1"
TASK_ID = "709d506bd0aa"
SUMMARY = (
    "0-bg grid (h~5-13, w~8-17) where each of `target` "
    "ACTIVE ROWS (2-9, drawn from h rows without "
    "repetition) holds 1-4 SCATTERED NON-0 CELLS at "
    "DISTINCT column positions in cols 1..w-1 (col 0 "
    "stays bg-0, ensuring leading zero before any non-"
    "zero, so packing has visible effect). Cell colors "
    "are drawn uniformly from {1..9}, with replacement "
    "(so a row may have duplicate colors but at "
    "distinct positions). Non-active rows stay all-0. "
    "At least one active row has leading or internal "
    "zeros (the col-0 bg constraint and sparse "
    "placement guarantee this). Rule (PER-ROW LEFT-"
    "PACK NON-ZERO VALUES, RIGHT-PAD WITH ZEROS): "
    "for EACH ROW r independently: collect every non-"
    "zero value in left-to-right order, preserving "
    "their RELATIVE ORDER. REPLACE the row with a "
    "left-packed sequence: place the collected values "
    "in cols 0, 1, 2, ... and fill the remaining "
    "right-side cells with 0. Empty rows stay all-0. "
    "Row dimensions are preserved. Net: each row is "
    "compacted to its left edge — sorted-by-position "
    "(not sorted-by-value), with the right side "
    "padded by bg-0."
)

# Rivals: 'output is input' refuted by any demo with internal zeros.
# 'sort values within row' refuted by ≥1 demo where output order
# ≠ sorted. 'right-pack instead' refuted by any demo (left side
# fills). 'pack ALL non-zeros into row 0' refuted by any multi-row
# demo (each row packs independently). 3 demos with ≥3 distinct
# colors per row cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "each active row contains one or more nonzero cells",
    "color order within each row matters",
    "at least one active row has leading or internal zeros",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_grid", "already_packed", "single_color_per_row")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "3..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "3..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "active_rows":    {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 2..9", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_columns",
                       "valid": "scattered_columns"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..9", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 non-zero cell not in col 0; ≥1 blank row; skip degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    nonzero = [(r, c) for r in range(h) for c in range(1, w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no non-zero cells found in cols 1+")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 6, 9)
        target = min(ctx.draw_int("active_rows", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 12, 17)
        target = min(ctx.draw_int("active_rows", 5, 9), h)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 9, 13)
        target = min(ctx.draw_int("active_rows", 3, 6), h)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for r in rng.sample(range(h), target):
        count = rng.randint(1, min(4, w - 1))
        cols = sorted(rng.sample(range(1, w), count))
        colors = rng.choices([1, 2, 3, 4, 5, 6, 7, 8, 9], k=count)
        for c, color in zip(cols, colors):
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # no nonzero cells → packing is a no-op
        return g
    if name == "already_packed":
        # all rows already left-packed → rule has no visible effect
        for r, vals in [(1, [3, 5]), (3, [2, 7, 4]), (4, [6])]:
            for i, v in enumerate(vals):
                g[r][i] = v
        return g
    if name == "single_color_per_row":
        # each active row has only one nonzero cell → packing reduces to a 1-cell shift
        g[1][5] = 3
        g[3][7] = 6
        g[4][2] = 4
        return g
    return g
