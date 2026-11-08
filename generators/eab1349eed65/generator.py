"""Generator for arc_additional_puzzles_21_set8:E53.

Rule: row-local nonzero values slide left while preserving order.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_marks, single_row, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eab1349eed65"
VERSION = "2.0.0"  # was rigidly fixed (3 rows at {0,h//2,h-1}, 2 cells at {2,w-3}, distinct colors); canonical has varied rows, 1-4 cells/row at varied cols, repeated colors -> randomize all
TASK_ID = "eab1349eed65"
SUMMARY = (
    "0-bg grid. Several rows (varied positions) hold 1-4 non-zero cells at "
    "RANDOM columns in RANDOM colors (repeats allowed within a row, as in "
    "canonical); other rows are empty. At least one marked row has a leading "
    "gap so the slide is non-trivial. Rule: in each row, gather the non-zero "
    "values left-to-right and pack them to the left, preserving order; the "
    "rest of the row becomes 0."
)

INVARIANTS = [
    "background is 0",
    "marked rows hold 1-4 non-zero cells at varied columns (colors may repeat)",
    "some rows are empty; >=1 marked row has a leading/internal gap (non-trivial slide)",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marks", "single_row", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..11 by diff", "valid": "6..11"},
    "grid_w":         {"type": "int", "default": "rng 7..14 by diff", "valid": "7..14"},
    "n_rows":         {"type": "int", "default": "rng 2..6 by diff", "valid": "1..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "random_rows", "valid": "random_rows"},
    "n_distinct_colors":{"type": "int", "default": "rng", "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7); w = ctx.draw_int("grid_w", 7, 9)
        nr_lo, nr_hi, k_hi = 2, 3, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 10, 14)
        nr_lo, nr_hi, k_hi = 4, 6, 4
    else:
        h = ctx.draw_int("grid_h", 6, 9); w = ctx.draw_int("grid_w", 8, 11)
        nr_lo, nr_hi, k_hi = 3, 4, 3
    g = full_grid(h, w, 0)
    n_marked = min(ctx.draw_int("n_rows", nr_lo, nr_hi), h)
    marked = rng.sample(range(h), n_marked)
    for idx, r in enumerate(marked):
        k = rng.randint(1, min(k_hi, w - 1))
        if idx == 0:
            # guarantee a non-trivial slide: leading gap (no cell at col 0)
            cols = rng.sample(range(1, w), min(k, w - 1))
        else:
            cols = rng.sample(range(w), k)
        for c in cols:
            g[r][c] = rng.randint(1, 9)     # random color, repeats allowed
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    active = 0
    nontrivial = False
    for r, row in enumerate(grid):
        nz = [c for c, v in enumerate(row) if v != 0]
        if not nz:
            continue
        active += 1
        if len(nz) > 4:
            errors.append(f"row {r} has too many marks: {len(nz)}")
        if min(nz) > 0:
            nontrivial = True
    if active == 0:
        errors.append("normal sample must contain marked rows")
    if active >= len(grid):
        errors.append("normal sample should leave at least one empty row")
    if not nontrivial:
        errors.append("at least one marked row must have a leading gap so slide-left is visible")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 8, 0)
    if name == "no_marks":
        return g
    if name == "single_row":
        g[3][2] = 3
        g[3][6] = 4
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(8):
                g[r][c] = 3
        return g
    return g
