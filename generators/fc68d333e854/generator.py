"""Generator for arc_puzzle_bank_thirteenth21:E91 — mirror non-9 cells across row 9-axis.

Rule: rows with a 9 axis mirror their colored cells across that axis.

Combinatorial axes: grid size, number of active (9-axis) rows, axis
position per row, cell count + positions (EITHER side of the axis),
colors, and decoy rows with no axis (rule leaves them unchanged).
Degenerates: no_axis, mirror_already_filled, cells_both_sides.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fc68d333e854"
VERSION = "2.1.0"  # add executable invariants for row-axis mirror episodes.
TASK_ID = "fc68d333e854"
SUMMARY = (
    "0-bg grid (size varies). Several ACTIVE rows each contain exactly "
    "one color-9 AXIS marker plus 1-5 other colored cells (colors 1-8) "
    "placed on EITHER side of the axis; each such cell has an in-bounds, "
    "currently-empty MIRROR slot across the axis. Some grids also include "
    "DECOY rows that hold stray colored cells but NO 9 axis. Rule: for "
    "each row, find the LEFTMOST 9 (the axis). For every non-0/non-9 cell "
    "in that row, copy it to its mirror column (2*axis - c) when that "
    "destination is in-bounds and still empty. Rows without a 9 are left "
    "unchanged. Net: every axis row becomes left-right symmetric about "
    "its 9; decoy rows pass through untouched. (Was tiny grids, 2-3 rows, "
    "cells on one side only, near-fixed colors.)"
)

INVARIANTS = [
    "background is 0",
    "each active row contains exactly one color-9 axis marker",
    "every colored cell in an active row has an in-bounds, empty mirror slot across the axis",
    "no two colored cells in a row are mirror images of each other (collision-free)",
    "decoy rows contain no 9, so the rule leaves them unchanged",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_axis", "mirror_already_filled", "cells_both_sides")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-8 easy / 8-12 med / 10-16 hard", "valid": "3..18"},
    "grid_w":         {"type": "int", "default": "9-12 easy / 11-16 med / 14-22 hard", "valid": "5..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "rows":           {"type": "int", "default": "2-3 easy / 3-5 med / 5-9 hard", "valid": "1..16"},
    "decoy_rows":     {"type": "int", "default": "0 easy / 0-1 med / 1-2 hard", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "random 1..8 per cell", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "row_9axis_either_side_cells",
                       "valid": "row_9axis_either_side_cells"},
    "n_distinct_colors": {"type": "int", "default": "up to 8", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 9, 12)
        active = ctx.draw_int("rows", 2, 3)
        n_decoy = 0
        cell_hi = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 16)
        w = ctx.draw_int("grid_w", 14, 22)
        active = ctx.draw_int("rows", 5, 9)
        n_decoy = ctx.draw_int("decoy_rows", 1, 2)
        cell_hi = 5
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 11, 16)
        active = ctx.draw_int("rows", 3, 5)
        n_decoy = ctx.draw_int("decoy_rows", 0, 1)
        cell_hi = 4

    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    active = min(active, h)
    n_decoy = min(n_decoy, h - active)
    chosen = rng.sample(range(h), active + n_decoy)
    active_rows = chosen[:active]
    decoy_rows = chosen[active:]

    for r in active_rows:
        axis = rng.randint(1, w - 2)
        g[r][axis] = 9
        used = {axis}
        n_cells = rng.randint(1, cell_hi)
        placed = 0
        for _ in range(n_cells * 8):
            if placed >= n_cells:
                break
            c = rng.randint(0, w - 1)
            cc = 2 * axis - c           # mirror column across the axis
            if c in used or cc == axis or not (0 <= cc < w) or cc in used:
                continue
            g[r][c] = rng.randint(1, 8)
            used.add(c)
            used.add(cc)                # reserve the mirror slot so it stays empty
            placed += 1
        if placed == 0:                 # guarantee >=1 mirrorable cell
            for cand in range(w):
                cc = 2 * axis - cand
                if cand != axis and 0 <= cc < w and cc != axis:
                    g[r][cand] = rng.randint(1, 8)
                    break

    # Decoy rows: stray cells, NO 9 axis -> rule leaves the row unchanged.
    for r in decoy_rows:
        for _ in range(rng.randint(1, 2)):
            c = rng.randint(0, w - 1)
            if g[r][c] == 0:
                g[r][c] = rng.randint(1, 8)   # never 9 -> no axis in this row

    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 11
    g = full_grid(h, w, 0)
    if name == "no_axis":
        # cells but no 9-axis in any row → no mirror line
        g[1][2] = 4; g[3][3] = 6
        return g
    if name == "mirror_already_filled":
        # mirror destination already has cells → mirror would clobber, rule skips
        axis = w // 2
        g[1][axis] = 9
        g[1][axis - 2] = 4   # left
        g[1][axis + 2] = 6   # right (occupied target)
        return g
    if name == "cells_both_sides":
        # cells on both sides of axis → each mirrors to its own empty slot
        axis = w // 2
        g[2][axis] = 9
        g[2][axis - 2] = 4
        g[2][axis + 1] = 6
        g[2][axis + 3] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    active_rows = 0
    for r, row in enumerate(grid):
        axes = [c for c, v in enumerate(row) if v == 9]
        if len(axes) > 1:
            errors.append(f"row {r} has multiple axis markers")
            continue
        if not axes:
            continue
        active_rows += 1
        axis = axes[0]
        colored = [c for c, v in enumerate(row) if v not in (0, 9)]
        if not colored:
            errors.append(f"row {r} has an axis but no colored cells to mirror")
            continue
        for c in colored:
            cc = 2 * axis - c
            if not (0 <= cc < len(row)):
                errors.append(f"row {r} colored cell has out-of-bounds mirror")
                break
            if row[cc] != 0:
                errors.append(f"row {r} mirror target is already occupied")
                break
    min_rows = 5 if difficulty == "hard" else 2 if difficulty == "easy" else 3
    if active_rows < min_rows:
        errors.append(f"expected at least {min_rows} active rows, found {active_rows}")
    return errors
